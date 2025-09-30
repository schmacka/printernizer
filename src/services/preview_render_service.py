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

logger = structlog.get_logger(__name__)

# Optional imports with graceful degradation
try:
    import trimesh
    import numpy as np
    from matplotlib import pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from mpl_toolkits.mplot3d import Axes3D
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

        # GCODE rendering configuration
        self.gcode_config = {
            'enabled': True,  # Enabled for testing
            'max_lines': 10000,
            'line_color': '#007bff',
            'background_color': '#ffffff'
        }

        # Cache settings
        self.cache_duration = timedelta(days=30)
        self._render_timeout = 10  # seconds

        # Statistics
        self.stats = {
            'renders_generated': 0,
            'renders_cached': 0,
            'render_failures': 0
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
        Render GCODE toolpath visualization.

        Note: This is a simplified visualization showing the toolpath.
        For better performance, this is disabled by default.

        Args:
            file_path: Path to GCODE file
            size: Desired size

        Returns:
            PNG bytes or None
        """
        try:
            # Parse gcode and extract movement commands
            points = []
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                current_pos = [0.0, 0.0, 0.0]
                line_count = 0

                for line in f:
                    line_count += 1
                    if line_count > self.gcode_config['max_lines']:
                        break

                    # Parse G0/G1 movement commands
                    if line.startswith('G0 ') or line.startswith('G1 '):
                        parts = line.strip().split()
                        for part in parts[1:]:
                            if part.startswith('X'):
                                current_pos[0] = float(part[1:])
                            elif part.startswith('Y'):
                                current_pos[1] = float(part[1:])
                            elif part.startswith('Z'):
                                current_pos[2] = float(part[1:])

                        points.append(current_pos.copy())

            if not points:
                logger.warning(f"No toolpath points found in {file_path}")
                return None

            # Convert to numpy array
            points = np.array(points)

            # Create figure
            dpi = self.stl_config['dpi']
            fig_width = size[0] / dpi
            fig_height = size[1] / dpi

            fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi)
            ax = fig.add_subplot(111, projection='3d')

            # Plot toolpath
            ax.plot(points[:, 0], points[:, 1], points[:, 2],
                   color=self.gcode_config['line_color'], linewidth=0.5)

            # Styling
            fig.patch.set_facecolor(self.gcode_config['background_color'])
            ax.set_facecolor(self.gcode_config['background_color'])
            ax.set_axis_off()

            # Save
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', pad_inches=0.1)
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
        except:
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

            for cache_file in self.cache_dir.glob("*.png"):
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
        cache_size = sum(
            f.stat().st_size for f in self.cache_dir.glob("*.png") if f.is_file()
        )
        cache_count = len(list(self.cache_dir.glob("*.png")))

        return {
            **self.stats,
            'cache_size_mb': round(cache_size / (1024 * 1024), 2),
            'cache_file_count': cache_count,
            'rendering_available': RENDERING_AVAILABLE
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

        if 'cache_duration_days' in config:
            self.cache_duration = timedelta(days=config['cache_duration_days'])

        if 'render_timeout' in config:
            self._render_timeout = config['render_timeout']

        logger.info("Preview render service configuration updated")
