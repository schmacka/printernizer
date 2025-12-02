"""
Preview rendering service for 3D files.
Generates thumbnail images from STL, GCODE, and other 3D file formats.
"""
import asyncio
import hashlib
import os
from datetime import datetime, timedelta
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import structlog

from ..utils.gcode_analyzer import GcodeAnalyzer
from ..utils.config import get_settings

logger = structlog.get_logger(__name__)

# Optional imports with graceful degradation
try:
    import trimesh
    import numpy as np
    from matplotlib import pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from mpl_toolkits.mplot3d import Axes3D
    from PIL import Image
    RENDERING_AVAILABLE = True
except ImportError as e:
    RENDERING_AVAILABLE = False
    logger.warning(f"Preview rendering libraries not available: {e}")


class PreviewRenderService:
    """Service for generating preview thumbnails from 3D files."""

    def __init__(self, cache_dir: str = "data/preview-cache"):
        """Initialize preview render service."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Configuration
        self.thumbnail_sizes = {
            'large': (512, 512),
            'medium': (256, 256),
            'small': (200, 200)
        }

        # STL rendering configuration
        self.stl_config = {
            'camera_angle': (45, 45, 0),  # azimuth, elevation, roll
            'background_color': '#ffffff',
            'edge_color': '#333333',
            'face_color': '#6c757d',
            'edge_width': 0.5,
            'dpi': 100
        }

        # Load settings
        settings = get_settings()

        # GCODE rendering configuration
        self.gcode_config = {
            'enabled': True,  # Enabled for testing
            'max_lines': settings.gcode_render_max_lines,
            'line_color': '#007bff',
            'background_color': '#ffffff',
            'optimize_print_only': settings.gcode_optimize_print_only,
            'optimization_max_lines': settings.gcode_optimization_max_lines
        }

        # Initialize G-code analyzer
        self.gcode_analyzer = GcodeAnalyzer(optimize_enabled=self.gcode_config['optimize_print_only'])

        # Animated preview configuration
        self.animation_config = {
            'enabled': True,  # Enable multi-angle animated previews
            'angles': [0, 90, 180, 270],  # Azimuth angles to render
            'frame_duration': 500,  # Milliseconds per frame
            'elevation': 45,  # Fixed elevation angle
            'loop': 0,  # 0 = infinite loop
        }

        # Cache settings
        self.cache_duration = timedelta(days=30)
        self._render_timeout = 10  # seconds

        # Statistics
        self.stats = {
            'renders_generated': 0,
            'renders_cached': 0,
            'render_failures': 0,
            'animated_renders_generated': 0,
            'animated_renders_cached': 0
        }

    async def get_or_generate_preview(
        self,
        file_path: str,
        file_type: str,
        size: Tuple[int, int] = (512, 512)
    ) -> Optional[bytes]:
        """
        Get cached preview or generate new one.

        Args:
            file_path: Path to the 3D file
            file_type: Type of file (stl, gcode, bgcode, 3mf)
            size: Desired thumbnail size (width, height)

        Returns:
            PNG image as bytes, or None if generation failed
        """
        if not RENDERING_AVAILABLE:
            logger.warning("Preview rendering not available - libraries not installed")
            return None

        try:
            # Check cache first
            cache_key = self._get_cache_key(file_path, size)
            cache_path = self.cache_dir / f"{cache_key}.png"

            if cache_path.exists():
                # Check if cache is still valid
                file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
                if file_age < self.cache_duration:
                    logger.debug(f"Using cached preview: {cache_path}")
                    with open(cache_path, 'rb') as f:
                        self.stats['renders_cached'] += 1
                        return f.read()

            # Generate new preview
            logger.info(f"Generating preview for {file_path}", file_type=file_type, size=size)

            # Run rendering in executor to avoid blocking
            loop = asyncio.get_event_loop()
            preview_bytes = await asyncio.wait_for(
                loop.run_in_executor(None, self._render_file, file_path, file_type, size),
                timeout=self._render_timeout
            )

            if preview_bytes:
                # Cache the result
                with open(cache_path, 'wb') as f:
                    f.write(preview_bytes)

                self.stats['renders_generated'] += 1
                logger.info(f"Successfully generated and cached preview: {cache_path}")
                return preview_bytes
            else:
                self.stats['render_failures'] += 1
                return None

        except asyncio.TimeoutError:
            logger.error(f"Preview rendering timed out for {file_path}")
            self.stats['render_failures'] += 1
            return None
        except Exception as e:
            logger.error(f"Failed to generate preview for {file_path}: {e}", exc_info=True)
            self.stats['render_failures'] += 1
            return None

    async def get_or_generate_animated_preview(
        self,
        file_path: str,
        file_type: str,
        size: Tuple[int, int] = (512, 512)
    ) -> Optional[bytes]:
        """
        Get cached animated GIF preview or generate new one.

        Args:
            file_path: Path to the 3D file
            file_type: Type of file (stl, 3mf)
            size: Desired thumbnail size (width, height)

        Returns:
            GIF image as bytes, or None if generation failed
        """
        logger.info("Animated preview request",
                   file_path=file_path,
                   file_type=file_type,
                   cache_enabled=self.animation_config['enabled'],
                   size=size)

        if not RENDERING_AVAILABLE:
            logger.warning("Preview rendering not available - libraries not installed")
            return None

        if not self.animation_config['enabled']:
            logger.debug("Animated previews disabled")
            return None

        # Only generate animated previews for mesh files (STL, 3MF)
        file_type_lower = file_type.lower()
        if file_type_lower not in ['stl', '3mf']:
            logger.debug(f"Animated previews not supported for {file_type}")
            return None

        try:
            # Check cache first
            cache_key = self._get_cache_key(file_path, size)
            cache_path = self.cache_dir / f"{cache_key}-animated.gif"

            if cache_path.exists():
                # Check if cache is still valid
                file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
                if file_age < self.cache_duration:
                    logger.info("Serving cached animated GIF",
                               cache_path=str(cache_path),
                               age_minutes=file_age.total_seconds() / 60)
                    with open(cache_path, 'rb') as f:
                        self.stats['animated_renders_cached'] += 1
                        return f.read()

            # Generate new animated preview
            logger.info("Generating new animated GIF",
                       angles=self.animation_config['angles'],
                       frame_count=len(self.animation_config['angles']))

            # Run rendering in executor to avoid blocking
            loop = asyncio.get_event_loop()
            gif_bytes = await asyncio.wait_for(
                loop.run_in_executor(None, self._render_animated_file, file_path, file_type, size),
                timeout=self._render_timeout * len(self.animation_config['angles'])  # More time for multiple frames
            )

            if gif_bytes:
                # Cache the result
                with open(cache_path, 'wb') as f:
                    f.write(gif_bytes)

                self.stats['animated_renders_generated'] += 1
                logger.info("Animated GIF generated successfully",
                           size_bytes=len(gif_bytes),
                           cache_path=str(cache_path))
                return gif_bytes
            else:
                self.stats['render_failures'] += 1
                logger.error("Animated GIF generation returned None")
                return None

        except asyncio.TimeoutError:
            logger.error("Animated GIF rendering timed out",
                        file_path=file_path,
                        timeout_seconds=self._render_timeout * len(self.animation_config['angles']))
            self.stats['render_failures'] += 1
            return None
        except Exception as e:
            logger.error("Animated GIF generation failed",
                        file_path=file_path,
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True)
            self.stats['render_failures'] += 1
            return None

    def _render_animated_file(
        self,
        file_path: str,
        file_type: str,
        size: Tuple[int, int]
    ) -> Optional[bytes]:
        """
        Render file to animated GIF with multiple camera angles (synchronous, run in executor).

        Args:
            file_path: Path to the file
            file_type: File type (stl, 3mf)
            size: Desired size

        Returns:
            GIF bytes or None
        """
        try:
            # Load mesh
            file_type_lower = file_type.lower()
            if file_type_lower == 'stl':
                mesh = trimesh.load_mesh(file_path)
            elif file_type_lower == '3mf':
                mesh = trimesh.load(file_path)
                if isinstance(mesh, trimesh.Scene):
                    mesh = trimesh.util.concatenate(
                        [geom for geom in mesh.geometry.values() if isinstance(geom, trimesh.Trimesh)]
                    )
            else:
                logger.warning(f"Unsupported file type for animation: {file_type}")
                return None

            if mesh.is_empty:
                logger.warning(f"Empty mesh in file: {file_path}")
                return None

            # Generate frames for each angle
            frames = []
            angles = self.animation_config['angles']
            elevation = self.animation_config['elevation']

            for azimuth in angles:
                frame_bytes = self._render_mesh_at_angle(mesh, size, azimuth, elevation)
                if frame_bytes:
                    # Convert PNG bytes to PIL Image
                    frame_image = Image.open(BytesIO(frame_bytes))
                    frames.append(frame_image)
                else:
                    logger.warning(f"Failed to render frame at angle {azimuth}")

            if not frames:
                logger.error("No frames generated for animated preview")
                return None

            # Create GIF
            gif_buffer = BytesIO()
            frames[0].save(
                gif_buffer,
                format='GIF',
                save_all=True,
                append_images=frames[1:],
                duration=self.animation_config['frame_duration'],
                loop=self.animation_config['loop'],
                optimize=False  # Disable optimization for speed
            )

            gif_buffer.seek(0)
            logger.info(f"Generated animated GIF with {len(frames)} frames")
            return gif_buffer.read()

        except Exception as e:
            logger.error(f"Failed to render animated file {file_path}: {e}")
            return None

    def _render_mesh_at_angle(
        self,
        mesh: 'trimesh.Trimesh',
        size: Tuple[int, int],
        azimuth: float,
        elevation: float
    ) -> Optional[bytes]:
        """
        Render mesh at a specific camera angle.

        Args:
            mesh: Trimesh object (already centered and normalized)
            size: Desired size
            azimuth: Azimuth angle in degrees
            elevation: Elevation angle in degrees

        Returns:
            PNG bytes
        """
        try:
            # Clone mesh to avoid modifying original
            mesh_copy = mesh.copy()

            # Center and normalize
            mesh_copy.vertices -= mesh_copy.centroid
            scale = 1.0 / max(mesh_copy.extents)
            mesh_copy.vertices *= scale

            # Create figure
            dpi = self.stl_config['dpi']
            fig_width = size[0] / dpi
            fig_height = size[1] / dpi

            fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi)
            ax = fig.add_subplot(111, projection='3d')

            # Set colors
            fig.patch.set_facecolor(self.stl_config['background_color'])
            ax.set_facecolor(self.stl_config['background_color'])

            # Plot mesh
            ax.plot_trisurf(
                mesh_copy.vertices[:, 0],
                mesh_copy.vertices[:, 1],
                mesh_copy.vertices[:, 2],
                triangles=mesh_copy.faces,
                color=self.stl_config['face_color'],
                edgecolor=self.stl_config['edge_color'],
                linewidth=self.stl_config['edge_width'],
                alpha=0.9,
                shade=True
            )

            # Set camera angle
            ax.view_init(elev=elevation, azim=azimuth)
            ax.set_axis_off()

            # Set equal aspect ratio
            max_range = 0.5
            ax.set_xlim([-max_range, max_range])
            ax.set_ylim([-max_range, max_range])
            ax.set_zlim([-max_range, max_range])

            # Save to bytes
            buf = BytesIO()
            plt.savefig(
                buf,
                format='png',
                dpi=dpi,
                bbox_inches='tight',
                pad_inches=0.1,
                facecolor=self.stl_config['background_color']
            )
            plt.close(fig)

            buf.seek(0)
            return buf.read()

        except Exception as e:
            logger.error(f"Failed to render mesh at angle {azimuth}: {e}")
            return None

    def _render_file(
        self,
        file_path: str,
        file_type: str,
        size: Tuple[int, int]
    ) -> Optional[bytes]:
        """
        Render file to PNG bytes (synchronous, run in executor).

        Args:
            file_path: Path to the file
            file_type: File type (stl, gcode, bgcode)
            size: Desired size

        Returns:
            PNG bytes or None
        """
        file_type_lower = file_type.lower()

        if file_type_lower == 'stl':
            return self._render_stl(file_path, size)
        elif file_type_lower == '3mf':
            return self._render_3mf(file_path, size)
        elif file_type_lower in ['gcode', 'bgcode'] and self.gcode_config['enabled']:
            return self._render_gcode_toolpath(file_path, size)
        else:
            logger.warning(f"No renderer available for file type: {file_type}")
            return None

    def _render_stl(self, file_path: str, size: Tuple[int, int]) -> Optional[bytes]:
        """
        Render STL file to PNG thumbnail.

        Args:
            file_path: Path to STL file
            size: Desired thumbnail size

        Returns:
            PNG image as bytes
        """
        try:
            # Load STL file
            mesh = trimesh.load_mesh(file_path)

            if not mesh.is_empty:
                # Center the mesh
                mesh.vertices -= mesh.centroid

                # Normalize size to fit in unit cube
                scale = 1.0 / max(mesh.extents)
                mesh.vertices *= scale

                # Create figure with specified size
                dpi = self.stl_config['dpi']
                fig_width = size[0] / dpi
                fig_height = size[1] / dpi

                fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi)
                ax = fig.add_subplot(111, projection='3d')

                # Set background color
                fig.patch.set_facecolor(self.stl_config['background_color'])
                ax.set_facecolor(self.stl_config['background_color'])

                # Plot mesh
                ax.plot_trisurf(
                    mesh.vertices[:, 0],
                    mesh.vertices[:, 1],
                    mesh.vertices[:, 2],
                    triangles=mesh.faces,
                    color=self.stl_config['face_color'],
                    edgecolor=self.stl_config['edge_color'],
                    linewidth=self.stl_config['edge_width'],
                    alpha=0.9,
                    shade=True
                )

                # Set camera angle
                azim, elev, roll = self.stl_config['camera_angle']
                ax.view_init(elev=elev, azim=azim)

                # Remove axes for cleaner look
                ax.set_axis_off()

                # Set equal aspect ratio
                max_range = 0.5
                ax.set_xlim([-max_range, max_range])
                ax.set_ylim([-max_range, max_range])
                ax.set_zlim([-max_range, max_range])

                # Save to bytes
                buf = BytesIO()
                plt.savefig(
                    buf,
                    format='png',
                    dpi=dpi,
                    bbox_inches='tight',
                    pad_inches=0.1,
                    facecolor=self.stl_config['background_color']
                )
                plt.close(fig)

                buf.seek(0)
                return buf.read()
            else:
                logger.warning(f"Empty mesh in STL file: {file_path}")
                return None

        except Exception as e:
            logger.error(f"Failed to render STL file {file_path}: {e}")
            return None

    def _render_3mf(self, file_path: str, size: Tuple[int, int]) -> Optional[bytes]:
        """
        Render 3MF file by extracting and rendering its meshes.

        Args:
            file_path: Path to 3MF file
            size: Desired thumbnail size

        Returns:
            PNG image as bytes
        """
        try:
            # Load 3MF file (trimesh can handle this)
            mesh = trimesh.load(file_path)

            # 3MF might contain a scene with multiple meshes
            if isinstance(mesh, trimesh.Scene):
                # Combine all meshes in the scene
                mesh = trimesh.util.concatenate(
                    [geom for geom in mesh.geometry.values() if isinstance(geom, trimesh.Trimesh)]
                )

            if not mesh.is_empty:
                # Use the same rendering as STL
                # Temporarily store as STL-like rendering
                return self._render_mesh_common(mesh, size)
            else:
                logger.warning(f"Empty mesh in 3MF file: {file_path}")
                return None

        except Exception as e:
            logger.error(f"Failed to render 3MF file {file_path}: {e}")
            return None

    def _render_mesh_common(self, mesh: 'trimesh.Trimesh', size: Tuple[int, int]) -> Optional[bytes]:
        """
        Common mesh rendering logic for any trimesh object.

        Args:
            mesh: Trimesh object
            size: Desired size

        Returns:
            PNG bytes
        """
        try:
            # Center the mesh
            mesh.vertices -= mesh.centroid

            # Normalize size
            scale = 1.0 / max(mesh.extents)
            mesh.vertices *= scale

            # Create figure
            dpi = self.stl_config['dpi']
            fig_width = size[0] / dpi
            fig_height = size[1] / dpi

            fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi)
            ax = fig.add_subplot(111, projection='3d')

            # Set colors
            fig.patch.set_facecolor(self.stl_config['background_color'])
            ax.set_facecolor(self.stl_config['background_color'])

            # Plot
            ax.plot_trisurf(
                mesh.vertices[:, 0],
                mesh.vertices[:, 1],
                mesh.vertices[:, 2],
                triangles=mesh.faces,
                color=self.stl_config['face_color'],
                edgecolor=self.stl_config['edge_color'],
                linewidth=self.stl_config['edge_width'],
                alpha=0.9,
                shade=True
            )

            # Camera
            azim, elev, roll = self.stl_config['camera_angle']
            ax.view_init(elev=elev, azim=azim)
            ax.set_axis_off()

            # Aspect ratio
            max_range = 0.5
            ax.set_xlim([-max_range, max_range])
            ax.set_ylim([-max_range, max_range])
            ax.set_zlim([-max_range, max_range])

            # Save
            buf = BytesIO()
            plt.savefig(
                buf,
                format='png',
                dpi=dpi,
                bbox_inches='tight',
                pad_inches=0.1,
                facecolor=self.stl_config['background_color']
            )
            plt.close(fig)

            buf.seek(0)
            return buf.read()

        except Exception as e:
            logger.error(f"Failed to render mesh: {e}")
            return None

    def _render_gcode_toolpath(self, file_path: str, size: Tuple[int, int]) -> Optional[bytes]:
        """
        Render GCODE toolpath visualization with optional print optimization.

        Args:
            file_path: Path to GCODE file
            size: Desired size

        Returns:
            PNG bytes or None
        """
        try:
            logger.info(f"Rendering G-code toolpath: {file_path}", 
                       optimize_enabled=self.gcode_config['optimize_print_only'])
            
            # Read and potentially optimize G-code
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    # Limit lines for performance, but analyze more for optimization
                    max_lines = (self.gcode_config['optimization_max_lines'] 
                               if self.gcode_config['optimize_print_only'] 
                               else self.gcode_config['max_lines'])
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip())
            
            # Apply G-code optimization if enabled
            if self.gcode_config['optimize_print_only']:
                original_count = len(lines)
                lines = self.gcode_analyzer.get_optimized_gcode_lines(lines)
                
                # Extend to max_lines from optimized start if needed
                if len(lines) < self.gcode_config['max_lines']:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        all_lines = f.readlines()
                        start_idx = original_count - len(lines)
                        end_idx = min(start_idx + self.gcode_config['max_lines'], len(all_lines))
                        lines = [line.rstrip() for line in all_lines[start_idx:end_idx]]
                        
                logger.info(f"G-code optimization applied: {original_count} -> {len(lines)} lines")
            
            # Parse movement commands
            points = []
            current_pos = [0.0, 0.0, 0.0]
            
            for line in lines:
                # Parse G0/G1 movement commands
                if line.startswith('G0 ') or line.startswith('G1 '):
                    parts = line.strip().split()
                    for part in parts[1:]:
                        try:
                            if part.startswith('X'):
                                current_pos[0] = float(part[1:])
                            elif part.startswith('Y'):
                                current_pos[1] = float(part[1:])
                            elif part.startswith('Z'):
                                current_pos[2] = float(part[1:])
                        except ValueError:
                            continue  # Skip invalid coordinates
                    
                    points.append(current_pos.copy())

            if not points:
                logger.warning(f"No toolpath points found in {file_path}")
                return None

            # Convert to numpy array
            points = np.array(points)
            logger.debug(f"Extracted {len(points)} toolpath points")

            # Create figure
            dpi = self.stl_config['dpi']
            fig_width = size[0] / dpi
            fig_height = size[1] / dpi

            fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi)
            ax = fig.add_subplot(111, projection='3d')

            # Plot toolpath
            ax.plot(points[:, 0], points[:, 1], points[:, 2],
                   color=self.gcode_config['line_color'], linewidth=0.5, alpha=0.8)

            # Styling
            fig.patch.set_facecolor(self.gcode_config['background_color'])
            ax.set_facecolor(self.gcode_config['background_color'])
            ax.set_axis_off()
            
            # Auto-fit the view
            if len(points) > 0:
                ax.set_xlim(points[:, 0].min(), points[:, 0].max())
                ax.set_ylim(points[:, 1].min(), points[:, 1].max())
                ax.set_zlim(points[:, 2].min(), points[:, 2].max())

            # Save
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', pad_inches=0.1,
                       facecolor=self.gcode_config['background_color'])
            plt.close(fig)

            buf.seek(0)
            return buf.read()

        except Exception as e:
            logger.error(f"Failed to render GCODE toolpath {file_path}: {e}")
            return None

    def _get_cache_key(self, file_path: str, size: Tuple[int, int]) -> str:
        """
        Generate cache key for a file and size.

        Args:
            file_path: File path
            size: Thumbnail size

        Returns:
            Cache key hash
        """
        # Include file path, size, and modification time in cache key
        try:
            mtime = os.path.getmtime(file_path)
        except (OSError, FileNotFoundError):
            # File not found or inaccessible, use 0 as fallback
            mtime = 0

        cache_string = f"{file_path}_{size[0]}x{size[1]}_{mtime}"
        return hashlib.md5(cache_string.encode()).hexdigest()

    async def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear preview cache.

        Args:
            older_than_days: Only clear files older than this many days.
                           If None, clear all.

        Returns:
            Number of files removed
        """
        removed_count = 0

        try:
            cutoff_time = None
            if older_than_days is not None:
                cutoff_time = datetime.now() - timedelta(days=older_than_days)

            # Clear both PNG and GIF cache files
            for pattern in ["*.png", "*.gif"]:
                for cache_file in self.cache_dir.glob(pattern):
                    if cache_file.is_file():
                        if cutoff_time is None:
                            # Remove all
                            cache_file.unlink()
                            removed_count += 1
                        else:
                            # Check age
                            file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                            if file_time < cutoff_time:
                                cache_file.unlink()
                                removed_count += 1

            logger.info(f"Cleared {removed_count} preview cache files")

        except Exception as e:
            logger.error(f"Error clearing preview cache: {e}")

        return removed_count

    def get_statistics(self) -> Dict[str, Any]:
        """Get rendering statistics."""
        png_files = list(self.cache_dir.glob("*.png"))
        gif_files = list(self.cache_dir.glob("*.gif"))

        cache_size = sum(f.stat().st_size for f in png_files + gif_files if f.is_file())
        cache_count = len(png_files) + len(gif_files)

        return {
            **self.stats,
            'cache_size_mb': round(cache_size / (1024 * 1024), 2),
            'cache_file_count': cache_count,
            'cache_png_count': len(png_files),
            'cache_gif_count': len(gif_files),
            'rendering_available': RENDERING_AVAILABLE,
            'animation_enabled': self.animation_config['enabled']
        }

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update service configuration.

        Args:
            config: Configuration dictionary
        """
        if 'stl_rendering' in config:
            self.stl_config.update(config['stl_rendering'])

        if 'gcode_rendering' in config:
            self.gcode_config.update(config['gcode_rendering'])
            # Update analyzer optimization setting
            if 'optimize_print_only' in config['gcode_rendering']:
                self.gcode_analyzer.optimize_enabled = config['gcode_rendering']['optimize_print_only']

        if 'animation' in config:
            self.animation_config.update(config['animation'])

        if 'cache_duration_days' in config:
            self.cache_duration = timedelta(days=config['cache_duration_days'])

        if 'render_timeout' in config:
            self._render_timeout = config['render_timeout']

        logger.info("Preview render service configuration updated")
