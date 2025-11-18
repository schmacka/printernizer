"""
File metadata service for extracting enhanced metadata from files.

This service is responsible for extracting comprehensive metadata from 3D files
including physical properties, print settings, material requirements, cost analysis,
quality metrics, and compatibility information.

Part of FileService refactoring - Phase 2 technical debt reduction.
Implements Phase 1 of Issue #43 - METADATA-001.
"""
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import structlog

from src.database.database import Database
from src.database.repositories import FileRepository
from src.services.event_service import EventService
from src.services.bambu_parser import BambuParser

logger = structlog.get_logger()


class FileMetadataService:
    """
    Service for extracting enhanced metadata from files.

    This service handles:
    - Extracting physical properties (dimensions, volume, weight)
    - Extracting print settings (layer height, infill, supports)
    - Extracting material requirements (filament type, weight, length)
    - Calculating cost breakdowns (material, energy, total)
    - Computing quality metrics (complexity, difficulty, success rate)
    - Determining compatibility info (printers, slicers, bed types)

    Supported file types:
    - 3MF files: Full metadata extraction via ThreeMFAnalyzer
    - G-code files: Metadata extraction via BambuParser
    - Future: STL/OBJ analysis

    Events Emitted:
    - file_metadata_extracted: When metadata is successfully extracted
    - metadata_extraction_failed: When extraction fails

    Example:
        >>> metadata_svc = FileMetadataService(database, event_service)
        >>> metadata = await metadata_svc.extract_enhanced_metadata("file_123")
        >>> print(metadata['physical_properties']['dimensions'])
    """

    def __init__(
        self,
        database: Database,
        event_service: EventService
    ):
        """
        Initialize file metadata service.

        Args:
            database: Database instance for storing metadata
            event_service: Event service for emitting metadata events
        """
        self.database = database
        self.file_repo = FileRepository(database._connection)
        self.event_service = event_service
        self.bambu_parser = BambuParser()

    async def extract_enhanced_metadata(
        self,
        file_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract enhanced metadata from a file using BambuParser and ThreeMFAnalyzer.

        This method implements Phase 1 of Issue #43 - METADATA-001.
        It extracts comprehensive metadata including physical properties, print settings,
        material requirements, cost analysis, quality metrics, and compatibility info.

        Args:
            file_id: ID of the file to analyze

        Returns:
            Enhanced metadata dictionary with keys:
                - physical_properties: Dimensions, volume, weight, object count
                - print_settings: Layer height, infill, supports, temperatures
                - material_requirements: Filament weight, length, multi-material flag
                - cost_breakdown: Material cost, energy cost, total cost
                - quality_metrics: Complexity score, difficulty level, success probability
                - compatibility_info: Compatible printers, slicer info, bed type
                - success: True if extraction succeeded

            Returns None if extraction failed or file not found

        Raises:
            None - All exceptions are caught and logged

        Example:
            >>> metadata = await metadata_svc.extract_enhanced_metadata("bambu_001_model.3mf")
            >>> if metadata and metadata.get('success'):
            ...     print(f"Complexity: {metadata['quality_metrics']['complexity_score']}")
        """
        try:
            from src.services.threemf_analyzer import ThreeMFAnalyzer
            from src.models.file import (
                EnhancedFileMetadata, PhysicalProperties, PrintSettings,
                MaterialRequirements, CostBreakdown, QualityMetrics, CompatibilityInfo
            )

            logger.info("Extracting enhanced metadata", file_id=file_id)

            # Get file record
            file_record = await self.file_repo.get(file_id)
            if not file_record:
                logger.error("File not found", file_id=file_id)
                return None

            file_path = file_record.get('file_path')
            if not file_path or not Path(file_path).exists():
                logger.warning("File path not found or does not exist",
                             file_id=file_id,
                             file_path=file_path)
                return None

            file_path = Path(file_path)
            file_type = file_path.suffix.lower()

            # Extract metadata based on file type
            enhanced_metadata = {}

            if file_type == '.3mf':
                enhanced_metadata = await self._extract_3mf_metadata(file_path)
            elif file_type in ['.gcode', '.g']:
                enhanced_metadata = await self._extract_gcode_metadata(file_path)
            else:
                logger.warning("Unsupported file type for enhanced metadata",
                             file_id=file_id,
                             file_type=file_type)
                return None

            if not enhanced_metadata or not enhanced_metadata.get('success'):
                return None

            # Convert to Pydantic models
            try:
                enhanced_model = EnhancedFileMetadata(
                    physical_properties=PhysicalProperties(**enhanced_metadata.get('physical_properties', {}))
                        if enhanced_metadata.get('physical_properties') else None,
                    print_settings=PrintSettings(**enhanced_metadata.get('print_settings', {}))
                        if enhanced_metadata.get('print_settings') else None,
                    material_requirements=MaterialRequirements(**enhanced_metadata.get('material_requirements', {}))
                        if enhanced_metadata.get('material_requirements') else None,
                    cost_breakdown=CostBreakdown(**enhanced_metadata.get('cost_breakdown', {}))
                        if enhanced_metadata.get('cost_breakdown') else None,
                    quality_metrics=QualityMetrics(**enhanced_metadata.get('quality_metrics', {}))
                        if enhanced_metadata.get('quality_metrics') else None,
                    compatibility_info=CompatibilityInfo(**enhanced_metadata.get('compatibility_info', {}))
                        if enhanced_metadata.get('compatibility_info') else None
                )

                # Update file record with enhanced metadata
                await self.file_repo.update_enhanced_metadata(
                    file_id=file_id,
                    enhanced_metadata=enhanced_model.model_dump(),
                    last_analyzed=datetime.now()
                )

                logger.info("Successfully extracted enhanced metadata", file_id=file_id)

                # Emit event
                await self.event_service.emit_event("file_metadata_extracted", {
                    "file_id": file_id,
                    "file_path": str(file_path),
                    "has_physical_properties": enhanced_model.physical_properties is not None,
                    "has_print_settings": enhanced_model.print_settings is not None,
                    "complexity_score": enhanced_model.quality_metrics.complexity_score
                        if enhanced_model.quality_metrics else None
                })

                return enhanced_model.model_dump()

            except Exception as e:
                logger.error("Failed to create metadata models",
                            file_id=file_id,
                            error=str(e))
                return None

        except Exception as e:
            logger.error("Failed to extract enhanced metadata",
                        file_id=file_id,
                        error=str(e))
            return None

    async def _extract_3mf_metadata(
        self,
        file_path: Path
    ) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from 3MF file using ThreeMFAnalyzer.

        Args:
            file_path: Path to the 3MF file

        Returns:
            Enhanced metadata dictionary or None if analysis fails
        """
        try:
            from src.services.threemf_analyzer import ThreeMFAnalyzer

            analyzer = ThreeMFAnalyzer()
            result = await analyzer.analyze_file(file_path)

            if result.get('success'):
                return result
            else:
                logger.warning("3MF analysis failed",
                             file_path=str(file_path),
                             error=result.get('error'))
                return None

        except Exception as e:
            logger.error("Failed to extract 3MF metadata",
                        file_path=str(file_path),
                        error=str(e))
            return None

    async def _extract_gcode_metadata(
        self,
        file_path: Path
    ) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from G-code file using BambuParser.

        Args:
            file_path: Path to the G-code file

        Returns:
            Enhanced metadata dictionary or None if parsing fails
        """
        try:
            result = await self.bambu_parser.parse_file(str(file_path))

            if not result.get('success'):
                logger.warning("G-code parsing failed",
                             file_path=str(file_path))
                return None

            metadata = result.get('metadata', {})

            # Convert parser output to enhanced metadata format
            enhanced_metadata = {
                'physical_properties': {
                    'width': metadata.get('model_width'),
                    'depth': metadata.get('model_depth'),
                    'height': metadata.get('model_height'),
                    'object_count': 1
                },
                'print_settings': {
                    'layer_height': metadata.get('layer_height'),
                    'first_layer_height': metadata.get('first_layer_height'),
                    'nozzle_diameter': metadata.get('nozzle_diameter'),
                    'wall_count': metadata.get('wall_loops'),
                    'wall_thickness': metadata.get('wall_thickness'),
                    'infill_density': metadata.get('infill_density') or metadata.get('sparse_infill_density'),
                    'infill_pattern': metadata.get('infill_pattern') or metadata.get('sparse_infill_pattern'),
                    'support_used': metadata.get('support_used') or metadata.get('enable_support'),
                    'nozzle_temperature': metadata.get('nozzle_temperature'),
                    'bed_temperature': metadata.get('bed_temperature'),
                    'print_speed': metadata.get('print_speed'),
                    'total_layer_count': metadata.get('total_layer_count')
                },
                'material_requirements': {
                    'total_weight': metadata.get('total_filament_weight_sum') or metadata.get('total_filament_used'),
                    'filament_length': metadata.get('filament_length_meters'),
                    'multi_material': isinstance(metadata.get('filament_used_grams', []), list) and
                                    len(metadata.get('filament_used_grams', [])) > 1
                },
                'cost_breakdown': {
                    'material_cost': metadata.get('material_cost_estimate'),
                    'energy_cost': metadata.get('energy_cost_estimate'),
                    'total_cost': metadata.get('total_cost_estimate')
                },
                'quality_metrics': {
                    'complexity_score': metadata.get('complexity_score'),
                    'difficulty_level': metadata.get('difficulty_level'),
                    'success_probability': 100 - (metadata.get('complexity_score', 5) * 5)
                        if metadata.get('complexity_score') else None
                },
                'compatibility_info': {
                    'compatible_printers': metadata.get('compatible_printers'),
                    'slicer_name': metadata.get('generator'),
                    'bed_type': metadata.get('curr_bed_type')
                },
                'success': True
            }

            return enhanced_metadata

        except Exception as e:
            logger.error("Failed to extract G-code metadata",
                        file_path=str(file_path),
                        error=str(e))
            return None

    def _extract_printer_info(
        self,
        printer: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Extract manufacturer and printer model from printer configuration.

        This is a utility method for extracting structured printer information
        from printer configuration dictionaries.

        Args:
            printer: Printer configuration dict with 'type' and 'name' fields

        Returns:
            Dict with keys:
                - manufacturer: Manufacturer identifier (e.g., 'bambu_lab', 'prusa_research')
                - printer_model: Model name (e.g., 'A1', 'Core One')

        Example:
            >>> info = metadata_svc._extract_printer_info({
            ...     'type': 'bambu_lab',
            ...     'name': 'Bambu Lab A1 Mini'
            ... })
            >>> print(info)
            {'manufacturer': 'bambu_lab', 'printer_model': 'A1 Mini'}
        """
        from src.models.printer import PrinterType

        manufacturer = 'unknown'
        printer_model = 'unknown'

        # Extract manufacturer from printer type
        printer_type = printer.get('type', 'unknown')
        if printer_type == PrinterType.BAMBU_LAB.value or printer_type == 'bambu_lab':
            manufacturer = 'bambu_lab'
        elif printer_type == PrinterType.PRUSA_CORE.value or printer_type == 'prusa_core':
            manufacturer = 'prusa_research'

        # Extract model from printer name or configuration
        printer_name = printer.get('name', '')

        # Common Bambu Lab models
        bambu_models = ['A1', 'A1 Mini', 'P1P', 'P1S', 'X1C', 'X1E']
        for model in bambu_models:
            if model.lower() in printer_name.lower():
                printer_model = model
                break

        # Common Prusa models
        prusa_models = ['Core One', 'MK4', 'MK3S', 'MK3', 'MINI', 'XL']
        for model in prusa_models:
            if model.lower() in printer_name.lower():
                printer_model = model
                break

        # If no model matched, use the printer name as fallback
        if printer_model == 'unknown' and printer_name:
            printer_model = printer_name

        return {
            'manufacturer': manufacturer,
            'printer_model': printer_model
        }
