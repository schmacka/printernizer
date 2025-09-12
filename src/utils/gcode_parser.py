"""
G-code parser for extracting thumbnails and metadata.
Supports PrusaSlicer, Bambu Studio, and other slicer formats.
"""
import re
import base64
import zipfile
from typing import Dict, Any, Optional, List
from pathlib import Path
import struct
import io


class GCodeParser:
    """Parser for G-code files to extract thumbnails and metadata."""
    
    def __init__(self):
        """Initialize the parser."""
        self.slicer_patterns = {
            'print_time': [
                r';.*print time.*:\s*(\d+)h\s*(\d+)m\s*(\d+)s',  # PrusaSlicer format
                r';.*print time.*:\s*(\d+)\s*minutes?',
                r';.*TIME:\s*(\d+)',  # Cura/others in seconds
                r';.*estimated printing time.*:\s*(\d+)h\s*(\d+)m'
            ],
            'material_used': [
                r';.*filament used.*=\s*(\d+\.?\d*)mm',  # PrusaSlicer
                r';.*material#\d+ used.*=\s*(\d+\.?\d*)g',  # Bambu Studio
                r';.*filament.*:\s*(\d+\.?\d*)\s*mm',
                r';\s*Filament_weight.*=\s*(\d+\.?\d*)'
            ],
            'layer_height': [
                r';.*layer_height.*=\s*(\d+\.?\d*)',
                r';.*Layer height.*:\s*(\d+\.?\d*)mm'
            ],
            'infill': [
                r';.*fill_density.*=\s*(\d+)',
                r';.*infill.*:\s*(\d+)%'
            ],
            'nozzle_temperature': [
                r';.*nozzle_temperature.*=\s*(\d+)',
                r';.*temperature.*:\s*(\d+)'
            ],
            'bed_temperature': [
                r';.*bed_temperature.*=\s*(\d+)',
                r';.*bed.*temp.*:\s*(\d+)'
            ],
            'material_type': [
                r';.*filament_type.*=\s*([A-Z]+)',
                r';.*material.*:\s*([A-Z][A-Z0-9]*)'
            ]
        }
    
    def parse_gcode_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a G-code file and extract thumbnails and metadata.
        
        Args:
            file_path: Path to the G-code file
            
        Returns:
            Dictionary containing thumbnails and metadata
        """
        try:
            path = Path(file_path)
            
            # Handle different file types
            if path.suffix.lower() == '.3mf':
                return self._parse_3mf_file(file_path)
            elif path.suffix.lower() in ['.gcode', '.bgcode']:
                return self._parse_gcode_text_file(file_path)
            else:
                return self._create_empty_result()
                
        except Exception as e:
            return {
                'error': str(e),
                'thumbnails': [],
                'metadata': {}
            }
    
    def _parse_gcode_text_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a text-based G-code file."""
        thumbnails = []
        metadata = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract thumbnails from comments
            thumbnails = self._extract_thumbnails_from_comments(content)
            
            # Extract metadata
            metadata = self._extract_metadata_from_comments(content)
            
            return {
                'thumbnails': thumbnails,
                'metadata': metadata
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'thumbnails': [],
                'metadata': {}
            }
    
    def _parse_3mf_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a 3MF file for thumbnails and metadata."""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                thumbnails = []
                metadata = {}
                
                # Look for thumbnail images
                for filename in zip_file.namelist():
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        with zip_file.open(filename) as img_file:
                            img_data = img_file.read()
                            thumbnail = {
                                'name': filename,
                                'size': len(img_data),
                                'format': Path(filename).suffix.lower()[1:],
                                'data': base64.b64encode(img_data).decode('ascii')
                            }
                            thumbnails.append(thumbnail)
                
                # Look for metadata in model files
                for filename in zip_file.namelist():
                    if filename.lower().endswith('.model'):
                        with zip_file.open(filename) as model_file:
                            model_content = model_file.read().decode('utf-8', errors='ignore')
                            metadata.update(self._extract_3mf_metadata(model_content))
                
                return {
                    'thumbnails': thumbnails,
                    'metadata': metadata
                }
                
        except Exception as e:
            return {
                'error': str(e),
                'thumbnails': [],
                'metadata': {}
            }
    
    def _extract_thumbnails_from_comments(self, content: str) -> List[Dict[str, Any]]:
        """Extract base64-encoded thumbnails from G-code comments."""
        thumbnails = []
        
        # PrusaSlicer thumbnail pattern
        prusa_pattern = r';\s*thumbnail begin (\d+)x(\d+) (\d+)\s*\n((?:;[^;\n]*\n)*?);\s*thumbnail end'
        
        for match in re.finditer(prusa_pattern, content, re.MULTILINE | re.DOTALL):
            width, height, size = match.groups()[:3]
            base64_lines = match.group(4)
            
            # Clean up the base64 data
            base64_data = ''.join(line.lstrip(';').strip() for line in base64_lines.split('\n') if line.strip())
            
            if base64_data:
                thumbnail = {
                    'name': f'thumbnail_{width}x{height}',
                    'width': int(width),
                    'height': int(height),
                    'size': int(size),
                    'format': 'png',  # Most thumbnails are PNG
                    'data': base64_data
                }
                thumbnails.append(thumbnail)
        
        # Bambu Studio thumbnail pattern (different format)
        bambu_pattern = r';\s*thumbnail_PNG begin (\d+) (\d+) (\d+) (\d+)\s*\n((?:;[^;\n]*\n)*?);\s*thumbnail_PNG end'
        
        for match in re.finditer(bambu_pattern, content, re.MULTILINE | re.DOTALL):
            width, height, size, _ = match.groups()[:4]
            base64_lines = match.group(5)
            
            base64_data = ''.join(line.lstrip(';').strip() for line in base64_lines.split('\n') if line.strip())
            
            if base64_data:
                thumbnail = {
                    'name': f'bambu_thumbnail_{width}x{height}',
                    'width': int(width), 
                    'height': int(height),
                    'size': int(size),
                    'format': 'png',
                    'data': base64_data
                }
                thumbnails.append(thumbnail)
        
        return thumbnails
    
    def _extract_metadata_from_comments(self, content: str) -> Dict[str, Any]:
        """Extract print metadata from G-code comments."""
        metadata = {}
        
        # Split content into lines for processing
        lines = content.split('\n')[:1000]  # Only check first 1000 lines for performance
        
        for line in lines:
            if not line.strip().startswith(';'):
                continue
                
            # Extract print time
            for pattern in self.slicer_patterns['print_time']:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    if len(match.groups()) >= 3:  # Hours, minutes, seconds format
                        hours = int(match.group(1))
                        minutes = int(match.group(2))
                        seconds = int(match.group(3)) if len(match.groups()) >= 3 else 0
                        metadata['estimated_print_time'] = hours * 3600 + minutes * 60 + seconds
                    elif len(match.groups()) == 2:  # Hours, minutes format
                        hours = int(match.group(1))
                        minutes = int(match.group(2))
                        metadata['estimated_print_time'] = hours * 3600 + minutes * 60
                    else:  # Single value (could be minutes or seconds)
                        value = int(match.group(1))
                        # Heuristic: if value > 1000, assume seconds, otherwise minutes
                        metadata['estimated_print_time'] = value if value > 1000 else value * 60
                    break
            
            # Extract material usage
            for pattern in self.slicer_patterns['material_used']:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    usage = float(match.group(1))
                    # Convert mm to grams (rough approximation: 1g ≈ 400mm for PLA)
                    if 'mm' in line.lower():
                        usage = usage / 400  # Convert mm to grams approximation
                    metadata['estimated_material_usage'] = round(usage, 2)
                    break
            
            # Extract other metadata
            for key, patterns in self.slicer_patterns.items():
                if key in ['print_time', 'material_used']:
                    continue
                    
                for pattern in patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        value = match.group(1)
                        try:
                            # Try to convert to number if possible
                            if '.' in value:
                                metadata[key] = float(value)
                            elif value.isdigit():
                                metadata[key] = int(value)
                            else:
                                metadata[key] = value
                        except ValueError:
                            metadata[key] = value
                        break
        
        return metadata
    
    def _extract_3mf_metadata(self, model_content: str) -> Dict[str, Any]:
        """Extract metadata from 3MF model content."""
        metadata = {}
        
        # Look for print settings in 3MF XML
        layer_height_match = re.search(r'layer_height["\'].*?value=["\']([^"\']+)', model_content)
        if layer_height_match:
            try:
                metadata['layer_height'] = float(layer_height_match.group(1))
            except ValueError:
                pass
        
        infill_match = re.search(r'fill_density["\'].*?value=["\']([^"\']+)', model_content)
        if infill_match:
            try:
                metadata['infill'] = float(infill_match.group(1)) * 100  # Convert to percentage
            except ValueError:
                pass
        
        return metadata
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Create an empty result structure."""
        return {
            'thumbnails': [],
            'metadata': {}
        }
    
    def validate_thumbnail_data(self, thumbnail_data: str) -> bool:
        """
        Validate that thumbnail data is valid base64-encoded image.
        
        Args:
            thumbnail_data: Base64-encoded image data
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Try to decode base64
            decoded = base64.b64decode(thumbnail_data)
            
            # Check for PNG signature
            if decoded.startswith(b'\x89PNG\r\n\x1a\n'):
                return True
            
            # Check for JPEG signature
            if decoded.startswith(b'\xff\xd8\xff'):
                return True
                
            return False
            
        except Exception:
            return False
    
    def get_thumbnail_dimensions(self, thumbnail_data: str) -> Optional[tuple]:
        """
        Get dimensions from thumbnail data.
        
        Args:
            thumbnail_data: Base64-encoded image data
            
        Returns:
            Tuple of (width, height) or None if couldn't be determined
        """
        try:
            decoded = base64.b64decode(thumbnail_data)
            
            # PNG format
            if decoded.startswith(b'\x89PNG\r\n\x1a\n'):
                # PNG IHDR chunk contains width and height
                width = struct.unpack('>I', decoded[16:20])[0]
                height = struct.unpack('>I', decoded[20:24])[0]
                return (width, height)
            
            # JPEG format - more complex, simplified approach
            elif decoded.startswith(b'\xff\xd8\xff'):
                # This is a simplified JPEG parser - may not work for all files
                i = 2
                while i < len(decoded) - 10:
                    if decoded[i:i+2] == b'\xff\xc0':  # Start of Frame marker
                        height = struct.unpack('>H', decoded[i+5:i+7])[0]
                        width = struct.unpack('>H', decoded[i+7:i+9])[0]
                        return (width, height)
                    i += 1
            
            return None
            
        except Exception:
            return None


# Global parser instance
gcode_parser = GCodeParser()


def parse_gcode_file(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to parse a G-code file.
    
    Args:
        file_path: Path to the G-code file
        
    Returns:
        Dictionary containing thumbnails and metadata
    """
    return gcode_parser.parse_gcode_file(file_path)