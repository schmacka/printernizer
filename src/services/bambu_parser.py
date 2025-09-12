"""
Bambu G-code and 3MF file parser for extracting thumbnails and metadata.
Supports parsing Bambu Lab slicer generated files for thumbnails and print information.
"""
import re
import base64
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from io import BytesIO
import structlog

logger = structlog.get_logger()


class BambuParser:
    """Parser for Bambu Lab G-code and 3MF files to extract thumbnails and metadata."""
    
    # G-code comment patterns for Bambu Lab files
    THUMBNAIL_PATTERN = re.compile(r'; thumbnail begin (\d+)x(\d+) (\d+)', re.MULTILINE)
    THUMBNAIL_END_PATTERN = re.compile(r'; thumbnail end', re.MULTILINE)
    
    # Metadata patterns from G-code comments
    METADATA_PATTERNS = {
        'estimated_time': re.compile(r'; estimated printing time \(normal mode\) = (.+)', re.IGNORECASE),
        'layer_height': re.compile(r'; layer_height = ([\d.]+)', re.IGNORECASE),
        'first_layer_height': re.compile(r'; first_layer_height = ([\d.]+)', re.IGNORECASE),
        'infill_density': re.compile(r'; fill_density = ([\d.]+)', re.IGNORECASE),
        'support_used': re.compile(r'; support_used = (.+)', re.IGNORECASE),
        'nozzle_temperature': re.compile(r'; nozzle_temperature_initial_layer = (\d+)', re.IGNORECASE),
        'bed_temperature': re.compile(r'; bed_temperature_initial_layer = (\d+)', re.IGNORECASE),
        'total_layer_count': re.compile(r'; total layer count = (\d+)', re.IGNORECASE),
        'print_speed': re.compile(r'; outer_wall_speed = ([\d.]+)', re.IGNORECASE),
    }
    
    # Filament usage patterns (Bambu AMS specific)
    FILAMENT_PATTERNS = {
        'filament_used': re.compile(r'; filament used \[g\] = ([\d.,]+)', re.IGNORECASE),
        'filament_cost': re.compile(r'; filament cost = ([\d.]+)', re.IGNORECASE),
        'filament_type': re.compile(r'; filament_type = (.+)', re.IGNORECASE),
        'filament_ids': re.compile(r'; filament_ids = (.+)', re.IGNORECASE),
    }
    
    def __init__(self):
        """Initialize the Bambu parser."""
        pass
    
    async def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a Bambu G-code or 3MF file and extract thumbnails and metadata.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Dictionary containing parsed data with keys:
            - thumbnails: List of thumbnail data (base64, width, height)
            - metadata: Dictionary of parsed metadata
            - success: Boolean indicating if parsing was successful
            - error: Error message if parsing failed
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f"File not found: {file_path}",
                    'thumbnails': [],
                    'metadata': {}
                }
            
            # Determine file type and parse accordingly
            if file_path.suffix.lower() == '.3mf':
                return await self._parse_3mf_file(file_path)
            elif file_path.suffix.lower() in ['.gcode', '.g']:
                return await self._parse_gcode_file(file_path)
            else:
                return {
                    'success': False,
                    'error': f"Unsupported file type: {file_path.suffix}",
                    'thumbnails': [],
                    'metadata': {}
                }
                
        except Exception as e:
            logger.error("Failed to parse file", file_path=str(file_path), error=str(e))
            return {
                'success': False,
                'error': str(e),
                'thumbnails': [],
                'metadata': {}
            }
    
    async def _parse_gcode_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse G-code file for thumbnails and metadata."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract thumbnails
            thumbnails = self._extract_gcode_thumbnails(content)
            
            # Extract metadata
            metadata = self._extract_gcode_metadata(content)
            
            logger.info("Successfully parsed G-code file", 
                       file_path=str(file_path), 
                       thumbnail_count=len(thumbnails),
                       metadata_keys=list(metadata.keys()))
            
            return {
                'success': True,
                'thumbnails': thumbnails,
                'metadata': metadata,
                'error': None
            }
            
        except Exception as e:
            logger.error("Failed to parse G-code file", file_path=str(file_path), error=str(e))
            return {
                'success': False,
                'error': str(e),
                'thumbnails': [],
                'metadata': {}
            }
    
    async def _parse_3mf_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse 3MF file for thumbnails and metadata."""
        try:
            thumbnails = []
            metadata = {}
            
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Look for thumbnail images in 3MF package
                thumbnail_files = [f for f in zip_file.namelist() 
                                 if f.startswith('Metadata/') and f.endswith('.png')]
                
                # Extract thumbnails
                for thumb_file in thumbnail_files:
                    try:
                        with zip_file.open(thumb_file) as thumb:
                            thumb_data = thumb.read()
                            thumb_base64 = base64.b64encode(thumb_data).decode('utf-8')
                            
                            # Try to get dimensions from filename or default
                            width, height = self._parse_thumbnail_dimensions(thumb_file)
                            
                            thumbnails.append({
                                'data': thumb_base64,
                                'width': width,
                                'height': height,
                                'format': 'png',
                                'source_file': thumb_file
                            })
                            
                    except Exception as e:
                        logger.warning("Failed to extract thumbnail from 3MF", 
                                     file=thumb_file, error=str(e))
                        continue
                
                # Parse 3MF model file for metadata
                try:
                    with zip_file.open('3D/3dmodel.model') as model_file:
                        model_content = model_file.read().decode('utf-8')
                        metadata.update(self._extract_3mf_metadata(model_content))
                except Exception as e:
                    logger.warning("Could not parse 3MF model metadata", error=str(e))
                
                # Look for other metadata files
                metadata_files = [f for f in zip_file.namelist() 
                                if f.startswith('Metadata/') and f.endswith('.xml')]
                
                for meta_file in metadata_files:
                    try:
                        with zip_file.open(meta_file) as meta:
                            meta_content = meta.read().decode('utf-8')
                            metadata.update(self._extract_3mf_metadata(meta_content))
                    except Exception as e:
                        logger.warning("Failed to parse 3MF metadata file", 
                                     file=meta_file, error=str(e))
                        continue
            
            logger.info("Successfully parsed 3MF file", 
                       file_path=str(file_path), 
                       thumbnail_count=len(thumbnails),
                       metadata_keys=list(metadata.keys()))
            
            return {
                'success': True,
                'thumbnails': thumbnails,
                'metadata': metadata,
                'error': None
            }
            
        except Exception as e:
            logger.error("Failed to parse 3MF file", file_path=str(file_path), error=str(e))
            return {
                'success': False,
                'error': str(e),
                'thumbnails': [],
                'metadata': {}
            }
    
    def _extract_gcode_thumbnails(self, content: str) -> List[Dict[str, Any]]:
        """Extract thumbnails from G-code comments."""
        thumbnails = []
        
        # Find all thumbnail sections
        thumbnail_matches = list(self.THUMBNAIL_PATTERN.finditer(content))
        thumbnail_end_matches = list(self.THUMBNAIL_END_PATTERN.finditer(content))
        
        if len(thumbnail_matches) != len(thumbnail_end_matches):
            logger.warning("Mismatched thumbnail begin/end markers", 
                          begin_count=len(thumbnail_matches),
                          end_count=len(thumbnail_end_matches))
            return thumbnails
        
        for i, begin_match in enumerate(thumbnail_matches):
            try:
                width = int(begin_match.group(1))
                height = int(begin_match.group(2))
                data_size = int(begin_match.group(3))
                
                if i < len(thumbnail_end_matches):
                    end_match = thumbnail_end_matches[i]
                    
                    # Extract the base64 data between begin and end
                    start_pos = begin_match.end()
                    end_pos = end_match.start()
                    thumbnail_section = content[start_pos:end_pos]
                    
                    # Clean up the data - remove comment markers and whitespace
                    thumbnail_data = ''
                    for line in thumbnail_section.split('\n'):
                        line = line.strip()
                        if line.startswith(';') and len(line) > 2:
                            # Remove comment marker and spaces
                            clean_line = line[1:].strip()
                            thumbnail_data += clean_line
                    
                    # Validate base64 data
                    if thumbnail_data and self._is_valid_base64(thumbnail_data):
                        thumbnails.append({
                            'data': thumbnail_data,
                            'width': width,
                            'height': height,
                            'format': 'png',
                            'data_size': data_size,
                            'source': 'gcode_comment'
                        })
                        
                        logger.debug("Extracted thumbnail from G-code", 
                                   width=width, height=height, data_size=data_size)
                    else:
                        logger.warning("Invalid base64 thumbnail data found")
                        
            except (ValueError, IndexError) as e:
                logger.warning("Failed to parse thumbnail", error=str(e))
                continue
        
        return thumbnails
    
    def _extract_gcode_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from G-code comments."""
        metadata = {}
        
        # Extract standard metadata
        for key, pattern in self.METADATA_PATTERNS.items():
            match = pattern.search(content)
            if match:
                value = match.group(1).strip()
                
                # Convert to appropriate type
                if key in ['layer_height', 'first_layer_height', 'infill_density', 'print_speed']:
                    try:
                        metadata[key] = float(value)
                    except ValueError:
                        metadata[key] = value
                elif key in ['nozzle_temperature', 'bed_temperature', 'total_layer_count']:
                    try:
                        metadata[key] = int(value)
                    except ValueError:
                        metadata[key] = value
                elif key == 'estimated_time':
                    metadata[key] = self._parse_time_duration(value)
                elif key == 'support_used':
                    metadata[key] = value.lower() in ['true', '1', 'yes']
                else:
                    metadata[key] = value
        
        # Extract filament information
        for key, pattern in self.FILAMENT_PATTERNS.items():
            match = pattern.search(content)
            if match:
                value = match.group(1).strip()
                
                if key == 'filament_used':
                    # Parse comma-separated list of filament usage per extruder
                    try:
                        filament_amounts = [float(x.strip()) for x in value.split(',')]
                        metadata['filament_used_grams'] = filament_amounts
                        metadata['total_filament_used'] = sum(filament_amounts)
                    except ValueError:
                        metadata[key] = value
                elif key == 'filament_cost':
                    try:
                        metadata[key] = float(value)
                    except ValueError:
                        metadata[key] = value
                elif key == 'filament_ids':
                    # Split AMS slot IDs
                    metadata['filament_ams_slots'] = [x.strip() for x in value.split(',')]
                else:
                    metadata[key] = value
        
        return metadata
    
    def _extract_3mf_metadata(self, xml_content: str) -> Dict[str, Any]:
        """Extract metadata from 3MF XML files."""
        metadata = {}
        
        try:
            root = ET.fromstring(xml_content)
            
            # Look for metadata elements
            for elem in root.iter():
                if 'metadata' in elem.tag.lower():
                    name = elem.get('name', '')
                    value = elem.text or elem.get('value', '')
                    
                    if name and value:
                        # Convert known numeric fields
                        if name.lower() in ['layer_height', 'layer_count', 'print_time', 
                                          'nozzle_temperature', 'bed_temperature']:
                            try:
                                if '.' in value:
                                    metadata[name.lower()] = float(value)
                                else:
                                    metadata[name.lower()] = int(value)
                            except ValueError:
                                metadata[name.lower()] = value
                        else:
                            metadata[name.lower()] = value
                            
        except ET.ParseError as e:
            logger.warning("Failed to parse 3MF XML metadata", error=str(e))
        
        return metadata
    
    def _parse_thumbnail_dimensions(self, filename: str) -> Tuple[int, int]:
        """Parse thumbnail dimensions from filename or return defaults."""
        # Try to extract dimensions from filename (e.g., thumbnail_200x200.png)
        dimension_match = re.search(r'(\d+)x(\d+)', filename)
        if dimension_match:
            return int(dimension_match.group(1)), int(dimension_match.group(2))
        
        # Default dimensions for 3MF thumbnails
        return 200, 200
    
    def _parse_time_duration(self, time_str: str) -> int:
        """Parse time duration string to seconds."""
        try:
            # Handle various time formats like "1h 30m 45s", "90m", "3600s", etc.
            time_str = time_str.lower().strip()
            total_seconds = 0
            
            # Extract hours
            hour_match = re.search(r'(\d+)h', time_str)
            if hour_match:
                total_seconds += int(hour_match.group(1)) * 3600
            
            # Extract minutes
            min_match = re.search(r'(\d+)m', time_str)
            if min_match:
                total_seconds += int(min_match.group(1)) * 60
            
            # Extract seconds
            sec_match = re.search(r'(\d+)s', time_str)
            if sec_match:
                total_seconds += int(sec_match.group(1))
            
            # If no time units found, assume it's just minutes
            if total_seconds == 0:
                try:
                    total_seconds = int(float(time_str)) * 60
                except ValueError:
                    total_seconds = 0
            
            return total_seconds
            
        except Exception as e:
            logger.warning("Failed to parse time duration", time_str=time_str, error=str(e))
            return 0
    
    def _is_valid_base64(self, s: str) -> bool:
        """Check if string is valid base64."""
        try:
            # Check if string length is multiple of 4 (after padding)
            if len(s) % 4 != 0:
                s += '=' * (4 - len(s) % 4)
            
            base64.b64decode(s, validate=True)
            return True
        except Exception:
            return False
    
    def get_largest_thumbnail(self, thumbnails: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get the largest thumbnail from a list of thumbnails."""
        if not thumbnails:
            return None
        
        # Find thumbnail with largest resolution
        largest = max(thumbnails, key=lambda t: t.get('width', 0) * t.get('height', 0))
        return largest
    
    def get_thumbnail_by_size(self, thumbnails: List[Dict[str, Any]], 
                             preferred_size: Tuple[int, int] = (200, 200)) -> Optional[Dict[str, Any]]:
        """Get thumbnail closest to preferred size."""
        if not thumbnails:
            return None
        
        preferred_width, preferred_height = preferred_size
        preferred_area = preferred_width * preferred_height
        
        # Find thumbnail with area closest to preferred
        closest = min(thumbnails, 
                     key=lambda t: abs((t.get('width', 0) * t.get('height', 0)) - preferred_area))
        
        return closest