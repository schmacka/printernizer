"""
German Business Logic Service
Handles German-specific business requirements including:
- Currency handling and formatting (EUR)
- VAT calculations (19% standard rate)
- Timezone handling (Europe/Berlin)
- German date/time formatting
- Business hours calculations
"""
import structlog
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional, List
import pytz
from zoneinfo import ZoneInfo

logger = structlog.get_logger()

# German business constants
GERMAN_VAT_RATE = Decimal('0.19')  # 19% standard VAT rate in Germany
GERMAN_TIMEZONE = 'Europe/Berlin'
GERMAN_LOCALE = 'de_DE'
CURRENCY_CODE = 'EUR'

# Business hours configuration (Mon-Fri, 9 AM - 5 PM)
DEFAULT_BUSINESS_HOURS = {
    'start_hour': 9,
    'end_hour': 17,
    'workdays': [0, 1, 2, 3, 4],  # Monday to Friday
}


def format_currency(amount: float, currency: str = 'EUR', locale: str = 'de_DE') -> str:
    """
    Format currency according to German standards.
    German format: 1.234,56 EUR (period for thousands, comma for decimals)
    
    Args:
        amount: The amount to format
        currency: Currency code (default: EUR)
        locale: Locale string (default: de_DE)
    
    Returns:
        Formatted currency string
    """
    try:
        # Convert to Decimal for precision
        decimal_amount = Decimal(str(amount))
        
        # Round to 2 decimal places
        rounded = decimal_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Split into integer and decimal parts
        integer_part = int(abs(rounded))
        decimal_part = int((abs(rounded) % 1) * 100)
        
        # Format integer part with German thousand separators (period)
        integer_str = f"{integer_part:,}".replace(',', '.')
        
        # Add negative sign if needed
        if rounded < 0:
            integer_str = '-' + integer_str
        
        # Combine with German decimal separator (comma)
        formatted = f"{integer_str},{decimal_part:02d} {currency}"
        
        logger.debug("currency_formatted", amount=amount, formatted=formatted)
        return formatted
    except Exception as e:
        logger.error("currency_format_error", amount=amount, error=str(e))
        return f"{amount:.2f} {currency}"


def round_currency(amount: Decimal, places: int = 2, rounding=ROUND_HALF_UP) -> Decimal:
    """
    Round currency amount to specified decimal places using German rounding rules.
    
    Args:
        amount: Amount to round
        places: Number of decimal places (default: 2 for EUR)
        rounding: Rounding mode (default: ROUND_HALF_UP for German standard)
    
    Returns:
        Rounded Decimal amount
    """
    try:
        quantize_str = '0.' + '0' * places
        rounded = amount.quantize(Decimal(quantize_str), rounding=rounding)
        logger.debug("currency_rounded", original=amount, rounded=rounded, places=places)
        return rounded
    except Exception as e:
        logger.error("currency_round_error", amount=amount, error=str(e))
        return amount


def handle_currency(amount: Decimal) -> Decimal:
    """
    Handle currency edge cases and normalization.
    Ensures currency amounts are properly formatted with 2 decimal places.
    
    Args:
        amount: Amount to handle
    
    Returns:
        Normalized Decimal amount
    """
    try:
        # Round to 2 decimal places
        normalized = round_currency(amount, places=2)
        
        # Ensure minimum of 0.01 for non-zero amounts
        if normalized != Decimal('0') and abs(normalized) < Decimal('0.01'):
            normalized = Decimal('0.01') if normalized > 0 else Decimal('-0.01')
        
        logger.debug("currency_handled", original=amount, normalized=normalized)
        return normalized
    except Exception as e:
        logger.error("currency_handle_error", amount=amount, error=str(e))
        return amount


def calculate_vat(net_amount: Decimal, vat_rate: Decimal = GERMAN_VAT_RATE) -> Dict[str, Decimal]:
    """
    Calculate VAT (MwSt) for given net amount.
    Standard German VAT rate is 19%.
    
    Args:
        net_amount: Net amount before VAT
        vat_rate: VAT rate as decimal (default: 0.19 for 19%)
    
    Returns:
        Dictionary with net_amount_eur, vat_rate, vat_amount_eur, gross_amount_eur
    """
    try:
        vat_amount = round_currency(net_amount * vat_rate)
        gross_amount = round_currency(net_amount + vat_amount)
        
        result = {
            'net_amount_eur': net_amount,
            'vat_rate': vat_rate,
            'vat_amount_eur': vat_amount,
            'gross_amount_eur': gross_amount
        }
        
        logger.debug("vat_calculated", **result)
        return result
    except Exception as e:
        logger.error("vat_calculation_error", net_amount=net_amount, vat_rate=vat_rate, error=str(e))
        raise


def calculate_net_from_gross(gross_amount: Decimal, vat_rate: Decimal = GERMAN_VAT_RATE) -> Dict[str, Decimal]:
    """
    Calculate net amount from gross amount including VAT (reverse calculation).
    
    Args:
        gross_amount: Gross amount including VAT
        vat_rate: VAT rate as decimal (default: 0.19 for 19%)
    
    Returns:
        Dictionary with gross_amount_eur, net_amount_eur, vat_amount_eur, vat_rate
    """
    try:
        # Net = Gross / (1 + VAT rate)
        divisor = Decimal('1') + vat_rate
        net_amount = round_currency(gross_amount / divisor)
        vat_amount = round_currency(gross_amount - net_amount)
        
        result = {
            'gross_amount_eur': gross_amount,
            'net_amount_eur': net_amount,
            'vat_amount_eur': vat_amount,
            'vat_rate': vat_rate
        }
        
        logger.debug("net_from_gross_calculated", **result)
        return result
    except Exception as e:
        logger.error("net_from_gross_error", gross_amount=gross_amount, vat_rate=vat_rate, error=str(e))
        raise


def calculate_vat_exempt(net_amount: Decimal, exemption_reason: str) -> Dict[str, Any]:
    """
    Calculate VAT for exempt transactions (0% VAT).
    Used for exports, certain services, etc.
    
    Args:
        net_amount: Net amount
        exemption_reason: Reason for VAT exemption
    
    Returns:
        Dictionary with amounts and exemption details
    """
    try:
        result = {
            'net_amount_eur': net_amount,
            'vat_rate': Decimal('0.00'),
            'vat_amount_eur': Decimal('0.00'),
            'gross_amount_eur': net_amount,
            'exemption_reason': exemption_reason
        }
        
        logger.info("vat_exempt_calculated", **result)
        return result
    except Exception as e:
        logger.error("vat_exempt_error", net_amount=net_amount, reason=exemption_reason, error=str(e))
        raise


def calculate_invoice_vat(line_items: List[Dict[str, Any]], vat_rate: Decimal = GERMAN_VAT_RATE) -> Dict[str, Any]:
    """
    Calculate VAT for complex invoices with multiple line items.
    
    Args:
        line_items: List of line items with 'description' and 'net_amount_eur'
        vat_rate: VAT rate as decimal (default: 0.19)
    
    Returns:
        Dictionary with line items, totals, and VAT breakdown
    """
    try:
        subtotal_net = Decimal('0')
        
        # Sum up all line items
        for item in line_items:
            net_amount = Decimal(str(item['net_amount_eur']))
            subtotal_net += net_amount
        
        # Calculate VAT
        total_vat = round_currency(subtotal_net * vat_rate)
        total_gross = round_currency(subtotal_net + total_vat)
        
        result = {
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
        
        logger.debug("invoice_vat_calculated", subtotal_net=subtotal_net, total_vat=total_vat, 
                    total_gross=total_gross, line_items_count=len(line_items))
        return result
    except Exception as e:
        logger.error("invoice_vat_error", line_items=line_items, error=str(e))
        raise


def to_berlin_timezone(dt: datetime) -> datetime:
    """
    Convert datetime to Europe/Berlin timezone.
    
    Args:
        dt: Datetime object (can be naive or aware)
    
    Returns:
        Datetime in Europe/Berlin timezone
    """
    try:
        berlin_tz = pytz.timezone(GERMAN_TIMEZONE)
        
        # If naive, assume it's UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Convert to Berlin timezone
        berlin_dt = dt.astimezone(berlin_tz)
        
        logger.debug("timezone_converted_to_berlin", original=dt, berlin=berlin_dt)
        return berlin_dt
    except Exception as e:
        logger.error("berlin_timezone_error", datetime=dt, error=str(e))
        raise


def from_berlin_timezone(dt: datetime) -> datetime:
    """
    Convert datetime from Europe/Berlin timezone to UTC.
    
    Args:
        dt: Datetime object in Berlin timezone
    
    Returns:
        Datetime in UTC timezone
    """
    try:
        # Ensure it's timezone-aware
        if dt.tzinfo is None:
            berlin_tz = pytz.timezone(GERMAN_TIMEZONE)
            dt = berlin_tz.localize(dt)
        
        # Convert to UTC
        utc_dt = dt.astimezone(timezone.utc)
        
        logger.debug("timezone_converted_from_berlin", berlin=dt, utc=utc_dt)
        return utc_dt
    except Exception as e:
        logger.error("from_berlin_timezone_error", datetime=dt, error=str(e))
        raise


def handle_dst_transition(dt: datetime, tz_name: str = GERMAN_TIMEZONE) -> Dict[str, Any]:
    """
    Handle daylight saving time transitions in German timezone.
    Germany uses DST: last Sunday in March (spring forward) and October (fall back).
    
    Args:
        dt: Datetime to check for DST transition
        tz_name: Timezone name (default: Europe/Berlin)
    
    Returns:
        Dictionary with transition information
    """
    try:
        tz = pytz.timezone(tz_name)
        
        # Check if this is during a DST transition
        # Spring forward: 2 AM becomes 3 AM (2 AM doesn't exist)
        # Fall back: 3 AM becomes 2 AM (2 AM happens twice)
        
        # Try to localize the datetime
        try:
            localized = tz.localize(dt, is_dst=None)
            is_valid = True
            is_ambiguous = False
            transition_type = 'none'
        except pytz.exceptions.NonExistentTimeError:
            # Spring forward - time doesn't exist
            is_valid = False
            is_ambiguous = False
            transition_type = 'spring_forward'
            localized = None
        except pytz.exceptions.AmbiguousTimeError:
            # Fall back - time happens twice
            is_valid = True
            is_ambiguous = True
            transition_type = 'fall_back'
            localized = tz.localize(dt, is_dst=True)  # Use DST time
        
        result = {
            'transition_type': transition_type,
            'local_time_before': dt if transition_type == 'spring_forward' else (dt - timedelta(hours=1) if transition_type == 'fall_back' else dt),
            'local_time_after': (dt + timedelta(hours=1)) if transition_type == 'spring_forward' else dt,
            'is_valid_time': is_valid,
            'is_ambiguous_time': is_ambiguous,
            'timezone': tz_name
        }
        
        logger.debug("dst_transition_handled", datetime=dt, **result)
        return result
    except Exception as e:
        logger.error("dst_transition_error", datetime=dt, timezone=tz_name, error=str(e))
        raise


def is_business_hours(dt: datetime, config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Check if given datetime is during German business hours.
    Default: Monday-Friday, 9 AM - 5 PM in Europe/Berlin timezone.
    
    Args:
        dt: Datetime to check (will be converted to Berlin timezone)
        config: Business hours configuration (optional)
    
    Returns:
        True if during business hours, False otherwise
    """
    try:
        if config is None:
            config = DEFAULT_BUSINESS_HOURS
        
        # Convert to Berlin timezone
        berlin_dt = to_berlin_timezone(dt)
        
        # Check if it's a workday
        if berlin_dt.weekday() not in config.get('workdays', DEFAULT_BUSINESS_HOURS['workdays']):
            return False
        
        # Check if it's within business hours
        start_hour = config.get('start_hour', DEFAULT_BUSINESS_HOURS['start_hour'])
        end_hour = config.get('end_hour', DEFAULT_BUSINESS_HOURS['end_hour'])
        
        is_business = start_hour <= berlin_dt.hour < end_hour
        
        logger.debug("business_hours_checked", datetime=berlin_dt, is_business_hours=is_business)
        return is_business
    except Exception as e:
        logger.error("business_hours_check_error", datetime=dt, error=str(e))
        return False


def calculate_business_duration(start: datetime, end: datetime, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Calculate business duration between two datetimes.
    Only counts hours during business hours (Monday-Friday, 9 AM - 5 PM).
    
    Args:
        start: Start datetime
        end: End datetime
        config: Business hours configuration (optional)
    
    Returns:
        Dictionary with total_hours, business_days, weekend_hours, holiday_hours
    """
    try:
        if config is None:
            config = DEFAULT_BUSINESS_HOURS
        
        # Convert to Berlin timezone
        start_berlin = to_berlin_timezone(start)
        end_berlin = to_berlin_timezone(end)
        
        # Initialize counters
        total_hours = 0.0
        business_days = 0
        weekend_hours = 0
        holiday_hours = 0
        
        # Count business hours day by day
        current = start_berlin.replace(hour=config.get('start_hour', 9), minute=0, second=0, microsecond=0)
        end_hour = config.get('end_hour', 17)
        
        while current < end_berlin:
            # Check if this is a business day
            if current.weekday() in config.get('workdays', DEFAULT_BUSINESS_HOURS['workdays']):
                # Count hours in this day
                day_start = max(current, start_berlin)
                day_end = min(current.replace(hour=end_hour), end_berlin)
                
                if day_start < day_end:
                    hours_in_day = (day_end - day_start).total_seconds() / 3600
                    total_hours += hours_in_day
                    
                    if hours_in_day >= (end_hour - config.get('start_hour', 9)) * 0.5:
                        business_days += 1
            
            # Move to next day
            current += timedelta(days=1)
            current = current.replace(hour=config.get('start_hour', 9), minute=0, second=0, microsecond=0)
        
        result = {
            'total_hours': round(total_hours, 2),
            'business_days': business_days,
            'weekend_hours': weekend_hours,
            'holiday_hours': holiday_hours
        }
        
        logger.debug("business_duration_calculated", start=start_berlin, end=end_berlin, **result)
        return result
    except Exception as e:
        logger.error("business_duration_error", start=start, end=end, error=str(e))
        raise


def format_german_date(dt: datetime) -> str:
    """
    Format date according to German standards: DD.MM.YYYY
    
    Args:
        dt: Datetime object
    
    Returns:
        Formatted date string (DD.MM.YYYY)
    """
    try:
        formatted = dt.strftime('%d.%m.%Y')
        logger.debug("german_date_formatted", datetime=dt, formatted=formatted)
        return formatted
    except Exception as e:
        logger.error("german_date_format_error", datetime=dt, error=str(e))
        return dt.isoformat()


def format_german_time(dt: datetime) -> str:
    """
    Format time according to German standards: HH:MM (24-hour format)
    
    Args:
        dt: Datetime object
    
    Returns:
        Formatted time string (HH:MM)
    """
    try:
        formatted = dt.strftime('%H:%M')
        logger.debug("german_time_formatted", datetime=dt, formatted=formatted)
        return formatted
    except Exception as e:
        logger.error("german_time_format_error", datetime=dt, error=str(e))
        return dt.strftime('%H:%M:%S')


def format_german_datetime(dt: datetime) -> str:
    """
    Format datetime according to German standards: DD.MM.YYYY HH:MM
    
    Args:
        dt: Datetime object
    
    Returns:
        Formatted datetime string (DD.MM.YYYY HH:MM)
    """
    try:
        date_part = format_german_date(dt)
        time_part = format_german_time(dt)
        formatted = f"{date_part} {time_part}"
        
        logger.debug("german_datetime_formatted", datetime=dt, formatted=formatted)
        return formatted
    except Exception as e:
        logger.error("german_datetime_format_error", datetime=dt, error=str(e))
        return dt.isoformat()
