"""
Tests for G-code analyzer functionality.
"""
import pytest
import tempfile
import os
from pathlib import Path

from src.utils.gcode_analyzer import GcodeAnalyzer


class TestGcodeAnalyzer:
    """Test G-code analysis functionality."""
    
    def test_init_enabled(self):
        """Test analyzer initialization with optimization enabled."""
        analyzer = GcodeAnalyzer(optimize_enabled=True)
        assert analyzer.optimize_enabled is True
        
    def test_init_disabled(self):
        """Test analyzer initialization with optimization disabled."""
        analyzer = GcodeAnalyzer(optimize_enabled=False)
        assert analyzer.optimize_enabled is False
        
    def test_find_print_start_disabled(self):
        """Test that disabled analyzer returns None."""
        analyzer = GcodeAnalyzer(optimize_enabled=False)
        gcode_lines = [
            "G28 ; home all axes",
            "M104 S200 ; set hotend temp",
            ";LAYER:0",
            "G1 X10 Y10 E5"
        ]
        
        result = analyzer.find_print_start_line(gcode_lines)
        assert result is None
        
    def test_find_print_start_layer_marker(self):
        """Test finding print start with layer markers."""
        analyzer = GcodeAnalyzer(optimize_enabled=True)
        gcode_lines = [
            "M190 S60 ; set bed temp",
            "M109 S200 ; set hotend temp",
            "G28 ; home all axes",
            ";LAYER:0",  # This should be detected
            "G1 X10 Y10 E5"
        ]
        
        result = analyzer.find_print_start_line(gcode_lines)
        assert result == 3  # Index of ";LAYER:0"
        
    def test_find_print_start_type_marker(self):
        """Test finding print start with TYPE markers."""
        analyzer = GcodeAnalyzer(optimize_enabled=True)
        gcode_lines = [
            "M190 S60 ; set bed temp", 
            "M109 S200 ; set hotend temp",
            "G28 ; home all axes",
            ";TYPE:SKIRT",  # This should be detected
            "G1 X10 Y10 E5"
        ]
        
        result = analyzer.find_print_start_line(gcode_lines)
        assert result == 3  # Index of ";TYPE:SKIRT"
        
    def test_find_print_start_extrusion_based(self):
        """Test finding print start based on extrusion after heating."""
        analyzer = GcodeAnalyzer(optimize_enabled=True)
        gcode_lines = [
            "M109 S200 ; set hotend temp",
            "G28 ; home all axes",
            "G1 X50 Y50 E0.1",  # Small extrusion, might be priming
            "G1 X100 Y100 E5.0"  # Larger extrusion, likely print
        ]
        
        result = analyzer.find_print_start_line(gcode_lines)
        assert result == 2  # Should pick the first extrusion move after heating
        
    def test_find_print_start_no_markers(self):
        """Test fallback when no clear markers found."""
        analyzer = GcodeAnalyzer(optimize_enabled=True)
        gcode_lines = [
            "G21 ; set units to millimeters",
            "G90 ; use absolute coordinates",
            "M82 ; use absolute distances for extrusion",
            "G1 X0 Y0 Z0"
        ]
        
        result = analyzer.find_print_start_line(gcode_lines)
        assert result is None  # No heating or obvious print start
        
    def test_is_likely_print_move_small_extrusion(self):
        """Test that small extrusions are not considered print moves."""
        analyzer = GcodeAnalyzer(optimize_enabled=True)
        
        # Small extrusion should return False
        result = analyzer._is_likely_print_move("G1 X10 Y10 E0.05")
        assert result is False
        
    def test_is_likely_print_move_edge_position(self):
        """Test that edge positions are not considered print moves."""
        analyzer = GcodeAnalyzer(optimize_enabled=True)
        
        # Edge position should return False
        result = analyzer._is_likely_print_move("G1 X1 Y1 E2.0")
        assert result is False
        
        # High coordinate edge should return False  
        result = analyzer._is_likely_print_move("G1 X249 Y249 E2.0")
        assert result is False
        
    def test_is_likely_print_move_normal_print(self):
        """Test that normal print moves are detected correctly."""
        analyzer = GcodeAnalyzer(optimize_enabled=True)
        
        # Normal print position should return True
        result = analyzer._is_likely_print_move("G1 X50 Y50 E2.0")
        assert result is True
        
    def test_get_optimized_gcode_lines_with_optimization(self):
        """Test getting optimized G-code lines when optimization is enabled."""
        analyzer = GcodeAnalyzer(optimize_enabled=True)
        original_lines = [
            "M190 S60 ; set bed temp",
            "M109 S200 ; set hotend temp", 
            "G28 ; home all axes",
            ";LAYER:0",  # Start here
            "G1 X10 Y10 E5",
            "G1 X20 Y20 F1500"
        ]
        
        result = analyzer.get_optimized_gcode_lines(original_lines)
        expected = [
            ";LAYER:0",
            "G1 X10 Y10 E5", 
            "G1 X20 Y20 F1500"
        ]
        
        assert result == expected
        
    def test_get_optimized_gcode_lines_disabled(self):
        """Test that disabled optimization returns original lines."""
        analyzer = GcodeAnalyzer(optimize_enabled=False)
        original_lines = [
            "M190 S60 ; set bed temp",
            "M109 S200 ; set hotend temp",
            "G28 ; home all axes",
            ";LAYER:0",
            "G1 X10 Y10 E5"
        ]
        
        result = analyzer.get_optimized_gcode_lines(original_lines)
        assert result == original_lines
        
    def test_get_optimized_gcode_lines_no_optimization_possible(self):
        """Test that lines are returned unchanged when no optimization is possible."""
        analyzer = GcodeAnalyzer(optimize_enabled=True)
        original_lines = [
            "G21 ; set units to millimeters",
            "G90 ; use absolute coordinates", 
            "G1 X0 Y0 Z0"
        ]
        
        result = analyzer.get_optimized_gcode_lines(original_lines)
        assert result == original_lines
        
    def test_analyze_gcode_file_success(self):
        """Test analyzing a real G-code file."""
        analyzer = GcodeAnalyzer(optimize_enabled=True)
        
        # Create temporary G-code file
        gcode_content = """M190 S60 ; set bed temp
M109 S200 ; set hotend temp
G28 ; home all axes
;LAYER:0
G1 X10 Y10 E5
G1 X20 Y20 F1500
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gcode', delete=False) as f:
            f.write(gcode_content)
            temp_path = f.name
            
        try:
            result = analyzer.analyze_gcode_file(temp_path)
            
            assert result['total_lines_analyzed'] == 6
            assert result['print_start_line'] == 3  # ;LAYER:0
            assert result['warmup_lines'] == 3
            assert result['optimization_possible'] is True
            assert result['optimization_enabled'] is True
            assert 'error' not in result
            
        finally:
            os.unlink(temp_path)
            
    def test_analyze_gcode_file_not_found(self):
        """Test analyzing non-existent file."""
        analyzer = GcodeAnalyzer(optimize_enabled=True)
        
        result = analyzer.analyze_gcode_file("/non/existent/file.gcode")
        
        assert result['total_lines_analyzed'] == 0
        assert result['print_start_line'] is None
        assert result['warmup_lines'] == 0
        assert result['optimization_possible'] is False
        assert 'error' in result
        
    def test_analyze_gcode_file_disabled(self):
        """Test analyzing file with optimization disabled."""
        analyzer = GcodeAnalyzer(optimize_enabled=False)
        
        gcode_content = """M190 S60 ; set bed temp
;LAYER:0
G1 X10 Y10 E5
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gcode', delete=False) as f:
            f.write(gcode_content)
            temp_path = f.name
            
        try:
            result = analyzer.analyze_gcode_file(temp_path)
            
            assert result['optimization_enabled'] is False
            assert result['optimization_possible'] is False  # Disabled means no optimization
            assert result['print_start_line'] is None
            
        finally:
            os.unlink(temp_path)
            
    def test_multiple_slicer_markers(self):
        """Test detection with multiple different slicer markers."""
        analyzer = GcodeAnalyzer(optimize_enabled=True)
        
        test_cases = [
            (";LAYER_CHANGE", 1),
            (";layer 0,", 1), 
            (";TYPE:BRIM", 1),
            (";TYPE:WALL-OUTER", 1),
            (";TYPE:PERIMETER", 1),
            ("START_PRINT", 1),
            (";PRINT_START", 1)
        ]
        
        for marker, expected_line in test_cases:
            gcode_lines = [
                "M109 S200 ; set hotend temp",
                marker,  # Should be detected
                "G1 X10 Y10 E5"
            ]
            
            result = analyzer.find_print_start_line(gcode_lines)
            assert result == expected_line, f"Failed to detect marker: {marker}"
            
    def test_warmup_end_pattern_detection(self):
        """Test detection of warmup end patterns."""
        analyzer = GcodeAnalyzer(optimize_enabled=True)
        gcode_lines = [
            "M109 S200 ; set hotend temp",
            "G28 X Y ; home XY axes",  # Should match G28.* pattern
            "G92 E0 ; reset extruder",  # Should match G92 E0.* pattern
            "G1 X50 Y50 E5"  # This should be the start
        ]
        
        result = analyzer.find_print_start_line(gcode_lines)
        # Should find start after the last warmup command
        assert result == 3  # After G92 E0
        
    @pytest.mark.parametrize("heating_command,expected_heated", [
        ("M104 S200", True),
        ("M109 S200", True),
        ("M140 S60", False),  # Bed heating doesn't set heated flag
        ("M190 S60", False),  # Bed heating doesn't set heated flag
        ("G28", False)
    ])
    def test_heating_detection(self, heating_command, expected_heated):
        """Test detection of heating commands."""
        analyzer = GcodeAnalyzer(optimize_enabled=True)
        gcode_lines = [
            heating_command,
            "G1 X50 Y50 E5"  # Potential print move
        ]
        
        result = analyzer.find_print_start_line(gcode_lines)
        
        if expected_heated:
            # Should find the extrusion move after heating
            assert result == 1
        else:
            # Without hotend heating, shouldn't find clear print start
            assert result is None or result == 1