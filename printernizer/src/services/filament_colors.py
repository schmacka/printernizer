"""
Filament color mapping for 3D printing filaments.

Maps filament IDs and names to standardized color values for better
file organization and visualization.
"""

from typing import Optional, List, Dict
import re


# Bambu Lab Filament ID → Color Mapping
# Based on Bambu Lab's filament ID system (GFL series)
BAMBU_FILAMENT_COLORS = {
    # Basic colors
    'GFL00': 'Black',
    'GFL01': 'White',
    'GFL02': 'Red',
    'GFL03': 'Orange',
    'GFL04': 'Yellow',
    'GFL05': 'Green',
    'GFL06': 'Blue',
    'GFL07': 'Purple',
    'GFL08': 'Gray',
    'GFL09': 'Pink',

    # Extended colors
    'GFL10': 'Brown',
    'GFL11': 'Cyan',
    'GFL12': 'Magenta',
    'GFL13': 'Lime',
    'GFL14': 'Navy',
    'GFL15': 'Teal',
    'GFL16': 'Maroon',
    'GFL17': 'Olive',
    'GFL18': 'Indigo',
    'GFL19': 'Turquoise',

    # Metallic/Special
    'GFL20': 'Silver',
    'GFL21': 'Gold',
    'GFL22': 'Bronze',
    'GFL23': 'Copper',

    # Transparent/Translucent
    'GFL30': 'Clear',
    'GFL31': 'Translucent White',
    'GFL32': 'Translucent Red',
    'GFL33': 'Translucent Blue',
    'GFL34': 'Translucent Green',
    'GFL35': 'Translucent Yellow',

    # Natural/Wood tones
    'GFL40': 'Natural',
    'GFL41': 'Beige',
    'GFL42': 'Tan',
    'GFL43': 'Ivory',

    # Specialized
    'GFL50': 'Glow in Dark',
    'GFL51': 'Color Changing',
    'GFL52': 'Carbon Fiber',
    'GFL53': 'Marble',
}

# Common color name variations and keywords
COLOR_KEYWORDS = {
    'black': 'Black',
    'white': 'White',
    'red': 'Red',
    'orange': 'Orange',
    'yellow': 'Yellow',
    'green': 'Green',
    'blue': 'Blue',
    'purple': 'Purple',
    'violet': 'Purple',
    'gray': 'Gray',
    'grey': 'Gray',
    'pink': 'Pink',
    'brown': 'Brown',
    'cyan': 'Cyan',
    'magenta': 'Magenta',
    'lime': 'Lime',
    'navy': 'Navy',
    'teal': 'Teal',
    'maroon': 'Maroon',
    'olive': 'Olive',
    'indigo': 'Indigo',
    'turquoise': 'Turquoise',
    'silver': 'Silver',
    'gold': 'Gold',
    'bronze': 'Bronze',
    'copper': 'Copper',
    'clear': 'Clear',
    'transparent': 'Clear',
    'translucent': 'Translucent',
    'natural': 'Natural',
    'beige': 'Beige',
    'tan': 'Tan',
    'ivory': 'Ivory',
    'glow': 'Glow in Dark',
    'marble': 'Marble',
    'wood': 'Wood Tone',
    'carbon': 'Carbon Fiber',
}


def extract_color_from_filament_id(filament_id: str) -> Optional[str]:
    """Extract color from Bambu Lab filament ID.

    Args:
        filament_id: Filament ID (e.g., "GFL00", "GFL02")

    Returns:
        Color name or None if not found

    Examples:
        >>> extract_color_from_filament_id("GFL00")
        'Black'
        >>> extract_color_from_filament_id("GFL02")
        'Red'
    """
    if not filament_id:
        return None

    # Clean up the ID
    filament_id = filament_id.strip().upper()

    # Look up in mapping
    return BAMBU_FILAMENT_COLORS.get(filament_id)


def extract_color_from_name(name: str) -> Optional[str]:
    """Extract color from filament or file name using keyword matching.

    Uses fuzzy matching to find color keywords in the name string.

    Args:
        name: Filament name or filename

    Returns:
        Color name or None if not detected

    Examples:
        >>> extract_color_from_name("Bambu PLA Basic - Black")
        'Black'
        >>> extract_color_from_name("red-dragon-model.3mf")
        'Red'
        >>> extract_color_from_name("multicolor-vase")
        None  # Can't determine single color
    """
    if not name:
        return None

    # Convert to lowercase for matching
    name_lower = name.lower()

    # Check for "multi" keyword - indicates multiple colors
    if 'multi' in name_lower or 'rainbow' in name_lower:
        return None  # Multiple colors, can't determine single color

    # Search for color keywords
    found_colors = []
    for keyword, color_name in COLOR_KEYWORDS.items():
        # Use word boundaries to avoid false matches
        # e.g., "Greenland" shouldn't match "Green"
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, name_lower):
            found_colors.append(color_name)

    # If we found exactly one color, return it
    if len(found_colors) == 1:
        return found_colors[0]

    # If multiple colors found, can't determine primary
    return None


def extract_colors_from_filament_ids(filament_ids: List[str]) -> List[str]:
    """Extract colors from a list of filament IDs.

    Args:
        filament_ids: List of filament IDs

    Returns:
        List of color names (may contain duplicates for multi-extruder setups)

    Examples:
        >>> extract_colors_from_filament_ids(["GFL00", "GFL02"])
        ['Black', 'Red']
    """
    colors = []

    for fid in filament_ids:
        color = extract_color_from_filament_id(fid)
        if color:
            colors.append(color)

    return colors


def get_primary_color(colors: List[str]) -> Optional[str]:
    """Get the primary (first/dominant) color from a list.

    Args:
        colors: List of color names

    Returns:
        Primary color or None if list is empty

    Examples:
        >>> get_primary_color(['Black', 'White', 'Red'])
        'Black'
        >>> get_primary_color([])
        None
    """
    if not colors:
        return None
    return colors[0]


def format_color_list(colors: List[str]) -> str:
    """Format a list of colors as a readable string.

    Args:
        colors: List of color names

    Returns:
        Formatted string

    Examples:
        >>> format_color_list(['Black'])
        'Black'
        >>> format_color_list(['Black', 'White'])
        'Black & White'
        >>> format_color_list(['Red', 'Green', 'Blue'])
        'Red, Green & Blue'
    """
    if not colors:
        return 'Unknown'

    if len(colors) == 1:
        return colors[0]

    if len(colors) == 2:
        return f"{colors[0]} & {colors[1]}"

    # More than 2 colors
    return ', '.join(colors[:-1]) + f" & {colors[-1]}"
