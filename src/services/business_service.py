"""
German Business Logic Service
Handles German-specific business requirements including:
- Currency handling (EUR)
- VAT calculations (19% standard rate)
- Timezone handling (Europe/Berlin)
- German accounting standards
- Date/time formatting
"""
import structlog
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
import pytz
from typing import Dict, Any, Optional, List

logger = structlog.get_logger()


# Currency Handling Functions

def format_currency(amount: float, currency: str = 'EUR', locale: str = 'de_DE') -> str:
    """
    Format currency according to German standards
    
    Args:
        amount: Amount to format
        currency: Currency code (default: EUR)
        locale: Locale for formatting (default: de_DE)
    
    Returns:
        Formatted currency string (e.g., "1.234,56 EUR")
    """
    # Convert to Decimal for precise handling
    decimal_amount = Decimal(str(amount))
    
    # Round to 2 decimal places
    rounded = decimal_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Format with German number formatting
    # German uses . as thousands separator and , as decimal separator
    integer_part = int(abs(rounded))
    decimal_part = abs(rounded) % 1
    
    # Format integer part with thousand separators
    integer_str = f"{integer_part:,}".replace(',', '.')
    
    # Add sign if negative
    if rounded < 0:
        integer_str = '-' + integer_str
    
    # Format decimal part
    decimal_str = f"{decimal_part:.2f}".split('.')[1]
    
    return f"{integer_str},{decimal_str} {currency}"


def round_currency(amount: Decimal, places: int = 2, rounding: str = ROUND_HALF_UP) -> Decimal:
    """
    Round currency to specified decimal places using German rounding rules
    
    Args:
        amount: Amount to round
        places: Number of decimal places (default: 2 for EUR)
        rounding: Rounding method (default: ROUND_HALF_UP)
    
    Returns:
        Rounded Decimal amount
    """
    quantizer = Decimal(10) ** -places
    return amount.quantize(quantizer, rounding=rounding)


def handle_currency(amount: Decimal) -> Decimal:
    """
    Handle currency edge cases and normalization
    
    Args:
        amount: Amount to handle
    
    Returns:
        Normalized Decimal amount
    """
    # Ensure minimum precision for EUR (0.01)
    rounded = round_currency(amount, places=2)
    
    # Ensure minimum value of 0.01 for positive amounts
    if 0 < rounded < Decimal('0.01'):
        return Decimal('0.01')
    
    return rounded


# VAT Calculation Functions

def calculate_vat(net_amount: Decimal, vat_rate: Decimal = Decimal('0.19')) -> Dict[str, Decimal]:
    """
    Calculate VAT (Mehrwertsteuer) for a net amount
    
    Args:
        net_amount: Net amount (without VAT)
        vat_rate: VAT rate (default: 0.19 for 19%)
    
    Returns:
        Dictionary with net_amount_eur, vat_rate, vat_amount_eur, gross_amount_eur
    """
    vat_amount = round_currency(net_amount * vat_rate, places=2)
    gross_amount = net_amount + vat_amount
    
    return {
        'net_amount_eur': net_amount,
        'vat_rate': vat_rate,
        'vat_amount_eur': vat_amount,
        'gross_amount_eur': gross_amount
    }


def calculate_net_from_gross(gross_amount: Decimal, vat_rate: Decimal = Decimal('0.19')) -> Dict[str, Decimal]:
    """
    Calculate net amount from gross amount (reverse VAT calculation)
    
    Args:
        gross_amount: Gross amount (including VAT)
        vat_rate: VAT rate (default: 0.19 for 19%)
    
    Returns:
        Dictionary with gross_amount_eur, net_amount_eur, vat_amount_eur, vat_rate
    """
    # Formula: net = gross / (1 + vat_rate)
    divisor = Decimal('1') + vat_rate
    net_amount = round_currency(gross_amount / divisor, places=2)
    vat_amount = gross_amount - net_amount
    
    return {
        'gross_amount_eur': gross_amount,
        'net_amount_eur': net_amount,
        'vat_amount_eur': vat_amount,
        'vat_rate': vat_rate
    }


def calculate_vat_exempt(net_amount: Decimal, exemption_type: str) -> Dict[str, Any]:
    """
    Calculate VAT for exempt transactions
    
    Args:
        net_amount: Net amount
        exemption_type: Type of exemption (e.g., 'export_non_eu')
    
    Returns:
        Dictionary with exemption details
    """
    exemption_reasons = {
        'export_non_eu': 'Export to non-EU country',
        'export_eu': 'Intra-community supply (reverse charge)',
        'small_business': 'Small business exemption (§19 UStG)',
        'exempt_service': 'VAT-exempt service'
    }
    
    return {
        'net_amount_eur': net_amount,
        'vat_rate': Decimal('0.00'),
        'vat_amount_eur': Decimal('0.00'),
        'gross_amount_eur': net_amount,
        'exemption_reason': exemption_reasons.get(exemption_type, 'VAT exempt')
    }


def calculate_invoice_vat(line_items: List[Dict[str, Any]], vat_rate: Decimal = Decimal('0.19')) -> Dict[str, Any]:
    """
    Calculate VAT for an invoice with multiple line items
    
    Args:
        line_items: List of line items with net_amount_eur
        vat_rate: VAT rate (default: 0.19)
    
    Returns:
        Dictionary with invoice totals and VAT breakdown
    """
    subtotal_net = Decimal('0')
    
    for item in line_items:
        subtotal_net += item['net_amount_eur']
    
    subtotal_net = round_currency(subtotal_net, places=2)
    total_vat = round_currency(subtotal_net * vat_rate, places=2)
    total_gross = subtotal_net + total_vat
    
    return {
        'line_items': line_items,
        'subtotal_net_eur': subtotal_net,
        'total_vat_eur': total_vat,
        'total_gross_eur': total_gross,
        'vat_breakdown': {
            '19%': {
                'net_amount_eur': subtotal_net,
                'vat_amount_eur': total_vat
            }
        }
    }


# Timezone Handling Functions

def to_berlin_timezone(dt: datetime) -> datetime:
    """
    Convert a datetime to Europe/Berlin timezone
    
    Args:
        dt: Datetime object (can be timezone-aware or naive)
    
    Returns:
        Datetime in Europe/Berlin timezone
    """
    berlin_tz = pytz.timezone('Europe/Berlin')
    
    # If naive, assume UTC
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    
    return dt.astimezone(berlin_tz)


def from_berlin_timezone(dt: datetime) -> datetime:
    """
    Convert a Berlin timezone datetime to UTC
    
    Args:
        dt: Datetime in Europe/Berlin timezone
    
    Returns:
        Datetime in UTC
    """
    berlin_tz = pytz.timezone('Europe/Berlin')
    
    # If naive, localize to Berlin first
    if dt.tzinfo is None:
        dt = berlin_tz.localize(dt)
    
    return dt.astimezone(pytz.utc)


def handle_dst_transition(dt: datetime, tz_name: str = 'Europe/Berlin') -> Dict[str, Any]:
    """
    Handle daylight saving time transitions
    
    Args:
        dt: Datetime to check
        tz_name: Timezone name
    
    Returns:
        Dictionary with transition information
    """
    tz = pytz.timezone(tz_name)
    
    # Check if this is during a DST transition
    # Spring forward: last Sunday in March at 2 AM
    # Fall back: last Sunday in October at 3 AM
    
    try:
        # Try to localize - will raise exception if time doesn't exist
        localized = tz.localize(dt, is_dst=None)
        is_valid = True
        is_ambiguous = False
    except pytz.exceptions.NonExistentTimeError:
        # Spring forward - time doesn't exist
        is_valid = False
        is_ambiguous = False
        transition_type = 'spring_forward'
        
        return {
            'transition_type': transition_type,
            'local_time_before': dt,
            'local_time_after': dt + timedelta(hours=1),
            'is_valid_time': is_valid,
            'timezone': tz_name
        }
    except pytz.exceptions.AmbiguousTimeError:
        # Fall back - time happens twice
        is_valid = True
        is_ambiguous = True
        transition_type = 'fall_back'
        
        return {
            'transition_type': transition_type,
            'local_time_before': dt + timedelta(hours=1),
            'local_time_after': dt,
            'is_ambiguous_time': is_ambiguous,
            'timezone': tz_name
        }
    
    return {
        'transition_type': 'none',
        'is_valid_time': is_valid,
        'is_ambiguous_time': is_ambiguous,
        'timezone': tz_name
    }


def is_business_hours(dt: datetime, config: Dict[str, Any]) -> bool:
    """
    Check if a datetime falls within business hours
    
    Args:
        dt: Datetime to check
        config: Business hours configuration
    
    Returns:
        True if within business hours, False otherwise
    """
    # Default German business hours: Monday-Friday, 9 AM - 5 PM
    business_start = config.get('business_hours_start', 9)
    business_end = config.get('business_hours_end', 17)
    
    # Convert to Berlin timezone if needed
    if dt.tzinfo is None or dt.tzinfo != pytz.timezone('Europe/Berlin'):
        dt = to_berlin_timezone(dt)
    
    # Check if weekend
    if dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Check if within business hours
    if business_start <= dt.hour < business_end:
        return True
    
    return False


def calculate_business_duration(start_time: datetime, end_time: datetime, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate duration counting only business hours
    
    Args:
        start_time: Start datetime
        end_time: End datetime
        config: Business hours configuration
    
    Returns:
        Dictionary with duration breakdown
    """
    business_hours_per_day = config.get('business_hours_per_day', 8)
    
    # Convert to Berlin timezone
    start_time = to_berlin_timezone(start_time)
    end_time = to_berlin_timezone(end_time)
    
    # Count business days
    business_days = 0
    current = start_time.date()
    end_date = end_time.date()
    
    while current <= end_date:
        # Check if weekday (Monday = 0, Friday = 4)
        if datetime.combine(current, datetime.min.time()).weekday() < 5:
            business_days += 1
        current += timedelta(days=1)
    
    total_hours = business_days * business_hours_per_day
    
    return {
        'total_hours': float(total_hours),
        'business_days': business_days,
        'weekend_hours': 0,
        'holiday_hours': 0
    }


# Date/Time Formatting Functions

def format_german_date(dt: datetime) -> str:
    """
    Format date according to German standards (DD.MM.YYYY)
    
    Args:
        dt: Datetime object
    
    Returns:
        Formatted date string
    """
    return dt.strftime('%d.%m.%Y')


def format_german_time(dt: datetime) -> str:
    """
    Format time according to German standards (24-hour format: HH:MM)
    
    Args:
        dt: Datetime object
    
    Returns:
        Formatted time string
    """
    return dt.strftime('%H:%M')


def format_german_datetime(dt: datetime) -> str:
    """
    Format datetime according to German standards (DD.MM.YYYY HH:MM)
    
    Args:
        dt: Datetime object
    
    Returns:
        Formatted datetime string
    """
    return f"{format_german_date(dt)} {format_german_time(dt)}"
