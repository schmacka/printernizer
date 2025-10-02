"""
3MF File Analyzer for extracting comprehensive metadata from 3MF packages.
Supports Bambu Lab and PrusaSlicer 3MF files with detailed analysis.
"""
import json
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import structlog

logger = structlog.get_logger()


class ThreeMFAnalyzer:
    """Comprehensive analyzer for 3MF files with enhanced metadata extraction."""
    
    def __init__(self):
        """Initialize the 3MF analyzer."""
        self.supported_extensions = ['.3mf']
    
    async def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze 3MF file and extract comprehensive metadata.
        
        Args:
            file_path: Path to the 3MF file
            
        Returns:
            Dictionary containing extracted metadata organized by category
        """
        metadata = {
            'physical_properties': {},
            'print_settings': {},
            'material_info': {},
            'compatibility': {},
            'cost_analysis': {},
            'quality_metrics': {},
            'success': False
        }
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Analyze different components of the 3MF package
                metadata['physical_properties'] = await self._analyze_model_geometry(zip_file)
                metadata['print_settings'] = await self._analyze_print_settings(zip_file)
                metadata['material_info'] = await self._analyze_material_usage(zip_file)
                metadata['compatibility'] = await self._analyze_compatibility(zip_file)
                
                # Calculate derived metrics
                metadata['cost_analysis'] = await self._calculate_costs(metadata)
                metadata['quality_metrics'] = await self._assess_quality(metadata)
                
                metadata['success'] = True
                logger.info("Successfully analyzed 3MF file", 
                          file_path=str(file_path),
                          objects=metadata['physical_properties'].get('object_count', 0))
                
        except FileNotFoundError:
            logger.error("3MF file not found", file_path=str(file_path))
            metadata['error'] = f"File not found: {file_path}"
        except zipfile.BadZipFile:
            logger.error("Invalid 3MF file (not a valid ZIP archive)", file_path=str(file_path))
            metadata['error'] = "Invalid 3MF file format"
        except Exception as e:
            logger.error("Failed to analyze 3MF file", 
                        file_path=str(file_path), 
                        error=str(e))
            metadata['error'] = str(e)
            
        return metadata
    
    async def _analyze_model_geometry(self, zip_file: zipfile.ZipFile) -> Dict[str, Any]:
        """Extract physical properties from 3MF model files."""
        geometry = {}
        
        try:
            # Try to parse Bambu Lab plate JSON for object layout
            if 'Metadata/plate_1.json' in zip_file.namelist():
                with zip_file.open('Metadata/plate_1.json') as f:
                    plate_data = json.loads(f.read().decode('utf-8'))
                    
                # Extract bounding box information
                if 'bbox_all' in plate_data:
                    bbox = plate_data['bbox_all']
                    geometry['model_width'] = round(bbox[2] - bbox[0], 2)
                    geometry['model_depth'] = round(bbox[3] - bbox[1], 2)
                    geometry['bounding_box'] = {
                        'min_x': bbox[0], 
                        'min_y': bbox[1],
                        'max_x': bbox[2], 
                        'max_y': bbox[3]
                    }
                
                # Extract object count and details
                if 'bbox_objects' in plate_data:
                    objects = plate_data['bbox_objects']
                    # Exclude wipe tower from count
                    geometry['object_count'] = len([
                        obj for obj in objects 
                        if obj.get('name') != 'wipe_tower'
                    ])
                    
                    total_area = 0
                    for obj in objects:
                        if obj.get('name') != 'wipe_tower':
                            total_area += obj.get('area', 0)
                    
                    geometry['total_print_area'] = round(total_area, 2)
                
                logger.debug("Extracted geometry from plate JSON", 
                           width=geometry.get('model_width'),
                           depth=geometry.get('model_depth'))
        
        except KeyError:
            logger.debug("Plate JSON not found in 3MF - may be PrusaSlicer format")
        except Exception as e:
            logger.warning("Could not extract geometry data", error=str(e))
            
        return geometry
    
    async def _analyze_print_settings(self, zip_file: zipfile.ZipFile) -> Dict[str, Any]:
        """Extract print settings from configuration files."""
        settings = {}
        
        try:
            # Try Bambu Lab process settings
            if 'Metadata/process_settings_1.config' in zip_file.namelist():
                with zip_file.open('Metadata/process_settings_1.config') as f:
                    config_data = json.loads(f.read().decode('utf-8'))
                    
                # Extract key print parameters with safe defaults
                settings['layer_height'] = self._safe_extract(config_data, 'layer_height', 0.2)
                settings['first_layer_height'] = self._safe_extract(config_data, 'first_layer_height', 0.2)
                settings['wall_loops'] = self._safe_extract(config_data, 'wall_loops', 2, as_int=True)
                settings['top_shell_layers'] = self._safe_extract(config_data, 'top_shell_layers', 3, as_int=True)
                settings['bottom_shell_layers'] = self._safe_extract(config_data, 'bottom_shell_layers', 3, as_int=True)
                settings['nozzle_diameter'] = self._safe_extract(config_data, 'nozzle_diameter', 0.4)
                
                # Extract infill settings
                infill_density = self._safe_extract(config_data, 'sparse_infill_density', '20%')
                if isinstance(infill_density, str) and '%' in infill_density:
                    settings['infill_density'] = float(infill_density.rstrip('%'))
                else:
                    settings['infill_density'] = float(infill_density) if infill_density else 20.0
                
                settings['infill_pattern'] = self._safe_extract(config_data, 'sparse_infill_pattern', 'gyroid')
                settings['support_used'] = config_data.get('enable_support', False)
                
                # Extract temperature settings
                settings['nozzle_temperature'] = self._safe_extract(config_data, 'nozzle_temperature', 210, as_int=True)
                settings['bed_temperature'] = self._safe_extract(config_data, 'bed_temperature', 60, as_int=True)
                settings['chamber_temperature'] = self._safe_extract(config_data, 'chamber_temperature', 0, as_int=True)
                
                # Extract speed settings
                settings['print_speed'] = self._safe_extract(config_data, 'outer_wall_speed', 50)
                settings['infill_speed'] = self._safe_extract(config_data, 'sparse_infill_speed', 100)
                settings['travel_speed'] = self._safe_extract(config_data, 'travel_speed', 150)
                
                # Calculate wall thickness
                if 'wall_loops' in settings and 'nozzle_diameter' in settings:
                    settings['wall_thickness'] = round(
                        settings['wall_loops'] * settings['nozzle_diameter'], 2
                    )
                
                logger.debug("Extracted print settings from 3MF config",
                           layer_height=settings.get('layer_height'),
                           nozzle=settings.get('nozzle_diameter'))
        
        except KeyError:
            logger.debug("Process settings not found in 3MF")
        except Exception as e:
            logger.warning("Could not extract print settings", error=str(e))
            
        return settings
    
    async def _analyze_material_usage(self, zip_file: zipfile.ZipFile) -> Dict[str, Any]:
        """Extract material and filament information."""
        material_info = {}
        
        try:
            # Parse Bambu Lab slice info for material data
            if 'Metadata/slice_info.config' in zip_file.namelist():
                with zip_file.open('Metadata/slice_info.config') as f:
                    slice_content = f.read().decode('utf-8')
                    
                # Parse XML content
                root = ET.fromstring(slice_content)
                plate = root.find('plate')
                
                if plate is not None:
                    # Extract weight and time predictions
                    weight_elem = plate.find("metadata[@key='weight']")
                    if weight_elem is not None:
                        material_info['estimated_weight'] = float(weight_elem.get('value', 0))
                    
                    prediction_elem = plate.find("metadata[@key='prediction']")
                    if prediction_elem is not None:
                        material_info['estimated_time'] = int(prediction_elem.get('value', 0))
                    
                    support_elem = plate.find("metadata[@key='support_used']")
                    if support_elem is not None:
                        material_info['support_used'] = support_elem.get('value', 'false') == 'true'
                    
                    # Extract filament mapping
                    filament_maps_elem = plate.find("metadata[@key='filament_maps']")
                    if filament_maps_elem is not None:
                        maps = filament_maps_elem.get('value', '').split()
                        material_info['filament_slots'] = [
                            int(slot) for slot in maps if slot.isdigit()
                        ]
            
            # Parse plate JSON for color information
            if 'Metadata/plate_1.json' in zip_file.namelist():
                with zip_file.open('Metadata/plate_1.json') as f:
                    plate_data = json.loads(f.read().decode('utf-8'))
                    
                material_info['filament_colors'] = plate_data.get('filament_colors', [])
                material_info['filament_ids'] = plate_data.get('filament_ids', [])
                
                logger.debug("Extracted material info from 3MF",
                           weight=material_info.get('estimated_weight'),
                           colors=len(material_info.get('filament_colors', [])))
        
        except Exception as e:
            logger.warning("Could not extract material usage", error=str(e))
            
        return material_info
    
    async def _analyze_compatibility(self, zip_file: zipfile.ZipFile) -> Dict[str, Any]:
        """Extract compatibility information."""
        compatibility = {}
        
        try:
            # Try to extract printer compatibility from config
            if 'Metadata/process_settings_1.config' in zip_file.namelist():
                with zip_file.open('Metadata/process_settings_1.config') as f:
                    config_data = json.loads(f.read().decode('utf-8'))
                    
                # Extract compatible printers
                printers = config_data.get('compatible_printers', [])
                if isinstance(printers, list):
                    compatibility['compatible_printers'] = printers
                elif isinstance(printers, str):
                    compatibility['compatible_printers'] = [
                        p.strip() for p in printers.split(',')
                    ]
                
                # Extract bed type
                compatibility['bed_type'] = config_data.get('curr_bed_type', 'Unknown')
                
                # Extract slicer information
                if 'generator' in config_data:
                    compatibility['slicer_name'] = config_data['generator']
                
                logger.debug("Extracted compatibility info", 
                           printers=len(compatibility.get('compatible_printers', [])))
        
        except Exception as e:
            logger.warning("Could not extract compatibility info", error=str(e))
            
        return compatibility
    
    async def _calculate_costs(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive cost breakdown."""
        costs = {
            'material_cost': 0.0,
            'energy_cost': 0.0,
            'total_cost': 0.0,
            'cost_per_gram': 0.0,
            'breakdown': {}
        }
        
        try:
            # Material cost calculation
            weight = metadata.get('material_info', {}).get('estimated_weight', 0)
            if weight and weight > 0:
                # Default material cost: €25/kg for PLA
                material_cost_per_kg = 25.0
                costs['material_cost'] = round((weight / 1000) * material_cost_per_kg, 2)
                costs['cost_per_gram'] = round(material_cost_per_kg / 1000, 3)
            
            # Energy cost calculation
            print_time = metadata.get('material_info', {}).get('estimated_time', 0)
            bed_temp = metadata.get('print_settings', {}).get('bed_temperature', 0)
            
            if print_time and print_time > 0:
                # Estimate power consumption (Watts)
                base_power = 50  # Base printer consumption
                heated_bed_power = 120 if bed_temp > 30 else 0
                hotend_power = 40
                
                total_power = base_power + heated_bed_power + hotend_power
                # Convert seconds to hours and calculate kWh
                energy_kwh = (total_power * print_time) / (1000 * 3600)
                # €0.30 per kWh (typical German electricity cost)
                energy_cost_per_kwh = 0.30
                costs['energy_cost'] = round(energy_kwh * energy_cost_per_kwh, 2)
            
            # Calculate total cost
            costs['total_cost'] = round(costs['material_cost'] + costs['energy_cost'], 2)
            
            # Detailed breakdown
            costs['breakdown'] = {
                'filament': costs['material_cost'],
                'electricity': costs['energy_cost'],
                'wear_and_tear': round(costs['total_cost'] * 0.05, 2),  # 5% for printer wear
                'labor': 0.0  # Can be configured for service providers
            }
            
            logger.debug("Calculated costs",
                       material_cost=costs['material_cost'],
                       energy_cost=costs['energy_cost'],
                       total=costs['total_cost'])
        
        except Exception as e:
            logger.warning("Could not calculate costs", error=str(e))
            
        return costs
    
    async def _assess_quality(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Assess print quality and difficulty metrics."""
        quality = {
            'complexity_score': 5,
            'difficulty_level': 'Intermediate',
            'success_probability': 85.0
        }
        
        try:
            print_settings = metadata.get('print_settings', {})
            material_info = metadata.get('material_info', {})
            
            # Calculate complexity score
            score = 5  # Base score
            
            # Layer height factor
            layer_height = print_settings.get('layer_height', 0.2)
            if layer_height <= 0.1:
                score += 2
            elif layer_height <= 0.15:
                score += 1
            elif layer_height >= 0.3:
                score -= 1
            
            # Support usage
            if print_settings.get('support_used') or material_info.get('support_used'):
                score += 1
            
            # Infill complexity
            infill_pattern = print_settings.get('infill_pattern', '').lower()
            if any(p in infill_pattern for p in ['gyroid', 'voronoi', 'lightning']):
                score += 1
            
            # High infill density
            if print_settings.get('infill_density', 20) > 80:
                score += 1
            
            # Multi-material printing
            filament_colors = material_info.get('filament_colors', [])
            if len(filament_colors) > 1:
                score += len(filament_colors) - 1
            
            # Clamp score
            quality['complexity_score'] = max(1, min(10, score))
            
            # Determine difficulty level
            if quality['complexity_score'] <= 3:
                quality['difficulty_level'] = 'Beginner'
            elif quality['complexity_score'] <= 6:
                quality['difficulty_level'] = 'Intermediate'
            elif quality['complexity_score'] <= 8:
                quality['difficulty_level'] = 'Advanced'
            else:
                quality['difficulty_level'] = 'Expert'
            
            # Estimate success probability (inverse relationship with complexity)
            # Base 95% success rate, reduced by complexity
            quality['success_probability'] = round(
                max(60.0, 95.0 - (quality['complexity_score'] - 1) * 3.5), 1
            )
            
            logger.debug("Assessed quality metrics",
                       complexity=quality['complexity_score'],
                       difficulty=quality['difficulty_level'],
                       success_rate=quality['success_probability'])
        
        except Exception as e:
            logger.warning("Could not assess quality", error=str(e))
            
        return quality
    
    def _safe_extract(self, data: dict, key: str, default: Any, as_int: bool = False) -> Any:
        """Safely extract value from config dict, handling list values."""
        value = data.get(key, default)
        
        # Handle list values (common in Bambu configs)
        if isinstance(value, list) and len(value) > 0:
            value = value[0]
        
        # Convert to int if requested
        if as_int and value is not None:
            try:
                return int(float(value)) if isinstance(value, (str, float)) else int(value)
            except (ValueError, TypeError):
                return default
        
        # Convert to float for numeric values
        if isinstance(value, str) and as_int is False:
            try:
                return float(value)
            except ValueError:
                pass
        
        return value if value is not None else default
