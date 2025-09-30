"""
G-code analyzer for identifying print start and warmup phases.
Used to optimize G-code preview rendering by showing only the actual print.
"""
import re
from typing import List, Optional, Tuple
import structlog

logger = structlog.get_logger(__name__)


class GcodeAnalyzer:
    """Analyzes G-code files to identify warmup vs actual printing phases."""
    
    # Common slicer markers that indicate print start
    PRINT_START_MARKERS = [
        ';LAYER:0',           # PrusaSlicer, Cura
        ';LAYER_CHANGE',      # PrusaSlicer
        ';layer 0,',          # Slic3r
        ';TYPE:SKIRT',        # Cura skirt
        ';TYPE:BRIM',         # Cura brim
        ';TYPE:WALL-OUTER',   # Cura outer perimeter
        ';TYPE:PERIMETER',    # Other slicers
        'START_PRINT',        # Custom start macro
        ';PRINT_START',       # Custom marker
    ]
    
    # Commands that typically end the warmup phase
    WARMUP_END_PATTERNS = [
        r'G28.*',             # Homing (usually last step)
        r'G29.*',             # Bed leveling
        r'M420.*',            # Bed leveling restore
        r'G92 E0.*',          # Reset extruder (often before print)
    ]
    
    def __init__(self, optimize_enabled: bool = True):
        """
        Initialize G-code analyzer.
        
        Args:
            optimize_enabled: Whether to enable print optimization
        """
        self.optimize_enabled = optimize_enabled
        
    def find_print_start_line(self, gcode_lines: List[str]) -> Optional[int]:
        """
        Find the line number where actual printing starts.
        
        Args:
            gcode_lines: List of G-code lines
            
        Returns:
            Line index where printing starts, or None if not found
        """
        if not self.optimize_enabled:
            return None
            
        heated = False
        bed_heated = False
        first_extrusion_after_heat = None
        last_warmup_command = None
        
        for i, line in enumerate(gcode_lines):
            line_upper = line.strip().upper()
            line_original = line.strip()
            
            # Check for slicer-specific markers (most reliable)
            for marker in self.PRINT_START_MARKERS:
                if marker.upper() in line_upper or marker in line_original:
                    logger.debug(f"Found print start marker '{marker}' at line {i + 1}")
                    return i
            
            # Track heating commands
            if line_upper.startswith('M104') or line_upper.startswith('M109'):  # Hotend
                heated = True
            elif line_upper.startswith('M140') or line_upper.startswith('M190'):  # Bed
                bed_heated = True
                
            # Check for warmup end patterns
            for pattern in self.WARMUP_END_PATTERNS:
                if re.match(pattern, line_upper):
                    last_warmup_command = i
                    
            # Look for first actual printing move (extrusion + movement after heating)
            if heated and line_upper.startswith('G1') and 'E' in line_upper:
                # Must have X or Y movement (not just Z or E-only moves)
                if ('X' in line_upper or 'Y' in line_upper):
                    if first_extrusion_after_heat is None:
                        first_extrusion_after_heat = i
                        
                    # Skip obvious priming moves (low E values, edge positions)
                    if self._is_likely_print_move(line_upper):
                        logger.debug(f"Found likely print start at line {i + 1}")
                        return i
        
        # Fallback strategies
        if last_warmup_command is not None:
            # Start after the last warmup command
            return last_warmup_command + 1
            
        if first_extrusion_after_heat is not None:
            # Use first extrusion after heating
            return first_extrusion_after_heat
            
        # No optimization possible
        logger.debug("Could not identify print start, will render entire G-code")
        return None
        
    def _is_likely_print_move(self, gcode_line: str) -> bool:
        """
        Determine if a G1 line is likely a print move vs priming.
        
        Args:
            gcode_line: Upper-case G-code line
            
        Returns:
            True if this looks like an actual print move
        """
        # Parse E value if present
        e_match = re.search(r'E([-\d.]+)', gcode_line)
        if e_match:
            try:
                e_value = float(e_match.group(1))
                # Skip very small extrusions (likely priming)
                if abs(e_value) < 0.1:
                    return False
            except ValueError:
                pass
                
        # Parse coordinates to detect edge positions (priming areas)
        x_match = re.search(r'X([-\d.]+)', gcode_line)
        y_match = re.search(r'Y([-\d.]+)', gcode_line)
        
        if x_match and y_match:
            try:
                x_val = float(x_match.group(1))
                y_val = float(y_match.group(1))
                
                # Skip moves at very low coordinates (often priming lines)
                if x_val < 5 and y_val < 5:
                    return False
                    
                # Skip moves at bed edges for common bed sizes
                if (x_val < 2 or x_val > 248 or  # 250mm bed
                    y_val < 2 or y_val > 248):
                    return False
                    
            except ValueError:
                pass
                
        return True
        
    def get_optimized_gcode_lines(self, gcode_lines: List[str]) -> List[str]:
        """
        Get G-code lines with warmup phase removed.
        
        Args:
            gcode_lines: Original G-code lines
            
        Returns:
            Optimized G-code lines (or original if optimization not possible)
        """
        if not self.optimize_enabled:
            return gcode_lines
            
        start_line = self.find_print_start_line(gcode_lines)
        
        if start_line is None:
            logger.debug("No print start found, returning full G-code")
            return gcode_lines
            
        optimized_lines = gcode_lines[start_line:]
        logger.info(f"G-code optimized: removed {start_line} warmup lines, "
                   f"kept {len(optimized_lines)} print lines")
        
        return optimized_lines
        
    def analyze_gcode_file(self, file_path: str, max_lines: int = 1000) -> dict:
        """
        Analyze a G-code file and return optimization info.
        
        Args:
            file_path: Path to G-code file
            max_lines: Maximum lines to analyze (for performance)
            
        Returns:
            Dictionary with analysis results
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip())
                    
            start_line = self.find_print_start_line(lines)
            
            return {
                'total_lines_analyzed': len(lines),
                'print_start_line': start_line,
                'warmup_lines': start_line if start_line else 0,
                'optimization_possible': start_line is not None,
                'optimization_enabled': self.optimize_enabled
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze G-code file {file_path}: {e}")
            return {
                'total_lines_analyzed': 0,
                'print_start_line': None,
                'warmup_lines': 0,
                'optimization_possible': False,
                'optimization_enabled': self.optimize_enabled,
                'error': str(e)
            }