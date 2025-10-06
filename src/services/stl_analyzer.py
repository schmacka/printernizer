"""
STL File Analyzer for extracting geometric metadata from STL files.
Uses Trimesh library for robust 3D mesh analysis.
"""
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()

# Optional import with graceful degradation
try:
    import trimesh
    import numpy as np
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False
    logger.warning("Trimesh not available - STL analysis will be limited")


class STLAnalyzer:
    """Analyzer for STL files to extract geometric metadata."""

    def __init__(self):
        """Initialize the STL analyzer."""
        self.supported_extensions = ['.stl']

    async def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze STL file and extract comprehensive geometric metadata.

        Args:
            file_path: Path to the STL file

        Returns:
            Dictionary containing extracted metadata organized by category
        """
        metadata = {
            'physical_properties': {},
            'geometry_info': {},
            'quality_metrics': {},
            'success': False
        }

        if not TRIMESH_AVAILABLE:
            metadata['error'] = "Trimesh library not available for STL analysis"
            logger.error("STL analysis attempted but Trimesh not available")
            return metadata

        try:
            # Run analysis in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            metadata = await loop.run_in_executor(None, self._analyze_stl_sync, file_path)

            logger.info("Successfully analyzed STL file",
                      file_path=str(file_path),
                      vertices=metadata.get('geometry_info', {}).get('vertex_count', 0))

        except FileNotFoundError:
            logger.error("STL file not found", file_path=str(file_path))
            metadata['error'] = f"File not found: {file_path}"
        except Exception as e:
            logger.error("Failed to analyze STL file",
                        file_path=str(file_path),
                        error=str(e))
            metadata['error'] = str(e)

        return metadata

    def _analyze_stl_sync(self, file_path: Path) -> Dict[str, Any]:
        """
        Synchronous STL analysis (runs in executor).

        Args:
            file_path: Path to STL file

        Returns:
            Metadata dictionary
        """
        metadata = {
            'physical_properties': {},
            'geometry_info': {},
            'quality_metrics': {},
            'success': False
        }

        try:
            # Load STL mesh
            mesh = trimesh.load_mesh(str(file_path))

            if mesh.is_empty:
                logger.warning("Empty mesh in STL file", file_path=str(file_path))
                metadata['error'] = "Empty mesh"
                return metadata

            # Extract physical properties (bounding box dimensions)
            bounds = mesh.bounds  # [[min_x, min_y, min_z], [max_x, max_y, max_z]]
            extents = mesh.extents  # [width, depth, height]

            metadata['physical_properties'] = {
                'model_width': round(float(extents[0]), 3),      # X dimension
                'model_depth': round(float(extents[1]), 3),      # Y dimension
                'model_height': round(float(extents[2]), 3),     # Z dimension
                'bounding_box': {
                    'min_x': round(float(bounds[0][0]), 3),
                    'min_y': round(float(bounds[0][1]), 3),
                    'min_z': round(float(bounds[0][2]), 3),
                    'max_x': round(float(bounds[1][0]), 3),
                    'max_y': round(float(bounds[1][1]), 3),
                    'max_z': round(float(bounds[1][2]), 3),
                },
                'center_of_mass': {
                    'x': round(float(mesh.centroid[0]), 3),
                    'y': round(float(mesh.centroid[1]), 3),
                    'z': round(float(mesh.centroid[2]), 3),
                },
            }

            # Calculate volume (convert mm³ to cm³)
            volume_mm3 = float(mesh.volume)
            metadata['physical_properties']['model_volume'] = round(volume_mm3 / 1000, 3)

            # Calculate surface area (convert mm² to cm²)
            surface_area_mm2 = float(mesh.area)
            metadata['physical_properties']['surface_area'] = round(surface_area_mm2 / 100, 3)

            # Extract geometry information
            metadata['geometry_info'] = {
                'vertex_count': len(mesh.vertices),
                'face_count': len(mesh.faces),
                'triangle_count': len(mesh.faces),  # STL uses triangles
                'edge_count': len(mesh.edges) if hasattr(mesh, 'edges') else None,
            }

            # Quality metrics
            metadata['quality_metrics'] = {
                'is_watertight': bool(mesh.is_watertight),
                'is_manifold': bool(mesh.is_watertight),  # Watertight implies manifold in most cases
                'has_normals': mesh.face_normals is not None,
            }

            # Try to detect if mesh has issues
            if hasattr(mesh, 'fill_holes'):
                # Check for holes (non-watertight)
                if not mesh.is_watertight:
                    metadata['quality_metrics']['has_holes'] = True
                    metadata['quality_metrics']['needs_repair'] = True
                else:
                    metadata['quality_metrics']['has_holes'] = False
                    metadata['quality_metrics']['needs_repair'] = False

            # Calculate complexity score based on geometry
            complexity = self._calculate_complexity(metadata)
            metadata['quality_metrics']['complexity_score'] = complexity
            metadata['quality_metrics']['difficulty_level'] = self._get_difficulty_level(complexity)

            # Estimate material usage if we had print settings
            # For now, just provide the volume which can be used for estimates
            # Typical PLA density is 1.24 g/cm³, but we don't know material or infill
            # This is just a rough estimate assuming 100% solid
            pla_density = 1.24  # g/cm³
            estimated_weight = volume_mm3 / 1000 * pla_density  # Volume in cm³ * density
            metadata['physical_properties']['estimated_solid_weight'] = round(estimated_weight, 2)

            metadata['success'] = True

            logger.debug("STL analysis complete",
                        volume=metadata['physical_properties']['model_volume'],
                        surface_area=metadata['physical_properties']['surface_area'],
                        vertices=metadata['geometry_info']['vertex_count'],
                        watertight=metadata['quality_metrics']['is_watertight'])

        except Exception as e:
            logger.error("Error during STL analysis", error=str(e))
            metadata['error'] = str(e)
            metadata['success'] = False

        return metadata

    def _calculate_complexity(self, metadata: Dict[str, Any]) -> int:
        """
        Calculate mesh complexity score (1-10 scale).
        Based on vertex count, surface area, and geometry quality.

        Args:
            metadata: Extracted metadata dictionary

        Returns:
            Complexity score from 1 (simple) to 10 (very complex)
        """
        score = 5  # Base score

        geometry = metadata.get('geometry_info', {})
        physical = metadata.get('physical_properties', {})
        quality = metadata.get('quality_metrics', {})

        # Vertex count factor
        vertex_count = geometry.get('vertex_count', 0)
        if vertex_count > 100000:
            score += 3  # Very high poly
        elif vertex_count > 50000:
            score += 2  # High poly
        elif vertex_count > 10000:
            score += 1  # Medium poly
        elif vertex_count < 1000:
            score -= 1  # Low poly (simpler)

        # Surface area to volume ratio (higher = more detail/complexity)
        volume = physical.get('model_volume', 0)
        surface_area = physical.get('surface_area', 0)
        if volume > 0 and surface_area > 0:
            sa_to_vol_ratio = surface_area / volume
            if sa_to_vol_ratio > 10:
                score += 1  # High detail/intricate geometry

        # Quality issues increase complexity
        if not quality.get('is_watertight', True):
            score += 1  # Non-manifold meshes are harder to print

        if quality.get('has_holes', False):
            score += 1  # Holes need repair

        # Clamp score to 1-10 range
        return max(1, min(10, score))

    def _get_difficulty_level(self, complexity: int) -> str:
        """
        Convert complexity score to difficulty level.

        Args:
            complexity: Complexity score (1-10)

        Returns:
            Difficulty level string
        """
        if complexity <= 3:
            return 'Beginner'
        elif complexity <= 6:
            return 'Intermediate'
        elif complexity <= 8:
            return 'Advanced'
        else:
            return 'Expert'
