"""
Unit tests for Business Service.
Tests German business logic including VAT calculations, currency formatting,
timezone handling, and business hours calculations.

Sprint 2 Phase 1 - Core Service Test Coverage.
"""
import pytest
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, timedelta
import pytz

from src.services.business_service import (
    format_currency,
    round_currency,
    handle_currency,
    calculate_vat,
    calculate_net_from_gross,
    calculate_vat_exempt,
    calculate_invoice_vat,
    to_berlin_timezone,
    from_berlin_timezone,
    handle_dst_transition,
    is_business_hours,
    calculate_business_duration,
    format_german_date,
    format_german_time,
    format_german_datetime,
    GERMAN_VAT_RATE,
    GERMAN_TIMEZONE,
    DEFAULT_BUSINESS_HOURS,
)


class TestCurrencyFormatting:
    """Test German currency formatting functions."""

    def test_format_currency_simple_amount(self):
        """Test formatting simple currency amounts."""
        result = format_currency(100.00)
        assert result == "100,00 EUR"

    def test_format_currency_with_decimals(self):
        """Test formatting amounts with decimal cents."""
        result = format_currency(19.99)
        assert result == "19,99 EUR"

    def test_format_currency_thousands_separator(self):
        """Test German thousand separator (period)."""
        result = format_currency(1234.56)
        assert result == "1.234,56 EUR"

    def test_format_currency_large_amount(self):
        """Test formatting large amounts with multiple thousands separators."""
        result = format_currency(1234567.89)
        assert result == "1.234.567,89 EUR"

    def test_format_currency_zero(self):
        """Test formatting zero amount."""
        result = format_currency(0.0)
        assert result == "0,00 EUR"

    def test_format_currency_negative_amount(self):
        """Test formatting negative amounts."""
        result = format_currency(-50.00)
        assert result == "-50,00 EUR"

    def test_format_currency_rounds_to_cents(self):
        """Test that amounts are rounded to 2 decimal places."""
        result = format_currency(10.999)
        assert result == "11,00 EUR"

    def test_format_currency_custom_currency_code(self):
        """Test formatting with custom currency code."""
        result = format_currency(100.00, currency='USD')
        assert result == "100,00 USD"


class TestCurrencyRounding:
    """Test currency rounding functions."""

    def test_round_currency_default_two_places(self):
        """Test default rounding to 2 decimal places."""
        result = round_currency(Decimal('10.456'))
        assert result == Decimal('10.46')

    def test_round_currency_half_up(self):
        """Test ROUND_HALF_UP rounding (German standard)."""
        # 0.5 rounds up
        result = round_currency(Decimal('10.455'))
        assert result == Decimal('10.46')

    def test_round_currency_three_places(self):
        """Test rounding to 3 decimal places."""
        result = round_currency(Decimal('10.4567'), places=3)
        assert result == Decimal('10.457')

    def test_round_currency_preserves_precision(self):
        """Test that rounding doesn't introduce floating point errors."""
        result = round_currency(Decimal('0.1') + Decimal('0.2'))
        assert result == Decimal('0.30')


class TestHandleCurrency:
    """Test currency normalization functions."""

    def test_handle_currency_normalizes_to_two_places(self):
        """Test normalization to 2 decimal places."""
        result = handle_currency(Decimal('10.5'))
        assert result == Decimal('10.50')

    def test_handle_currency_minimum_value(self):
        """Test minimum 0.01 for non-zero amounts after rounding.

        Note: 0.001 rounds to 0.00, then since it equals 0, minimum doesn't apply.
        The minimum only applies to amounts that are still non-zero after rounding.
        """
        # 0.006 rounds to 0.01 (not zero), so minimum applies
        result = handle_currency(Decimal('0.006'))
        assert result == Decimal('0.01')

    def test_handle_currency_very_small_rounds_to_zero(self):
        """Test that very small amounts round to zero."""
        # 0.001 rounds to 0.00, equals zero, stays zero
        result = handle_currency(Decimal('0.001'))
        assert result == Decimal('0.00')

    def test_handle_currency_zero_stays_zero(self):
        """Test that zero remains zero."""
        result = handle_currency(Decimal('0'))
        assert result == Decimal('0')

    def test_handle_currency_negative_minimum(self):
        """Test minimum -0.01 for small negative amounts after rounding.

        Note: -0.001 rounds to -0.00 (essentially 0), so minimum doesn't apply.
        """
        # -0.006 rounds to -0.01 (not zero), so minimum applies
        result = handle_currency(Decimal('-0.006'))
        assert result == Decimal('-0.01')

    def test_handle_currency_very_small_negative_rounds_to_zero(self):
        """Test that very small negative amounts round to zero."""
        result = handle_currency(Decimal('-0.001'))
        # Rounds to -0.00 which equals 0
        assert result == Decimal('0.00') or result == Decimal('-0.00')


class TestVATCalculations:
    """Test German VAT (MwSt) calculations."""

    def test_calculate_vat_standard_rate(self):
        """Test VAT calculation with standard 19% rate."""
        result = calculate_vat(Decimal('100.00'))

        assert result['net_amount_eur'] == Decimal('100.00')
        assert result['vat_rate'] == GERMAN_VAT_RATE
        assert result['vat_amount_eur'] == Decimal('19.00')
        assert result['gross_amount_eur'] == Decimal('119.00')

    def test_calculate_vat_custom_rate(self):
        """Test VAT calculation with custom rate (7% reduced)."""
        result = calculate_vat(Decimal('100.00'), vat_rate=Decimal('0.07'))

        assert result['vat_rate'] == Decimal('0.07')
        assert result['vat_amount_eur'] == Decimal('7.00')
        assert result['gross_amount_eur'] == Decimal('107.00')

    def test_calculate_vat_rounds_correctly(self):
        """Test VAT calculation rounds to 2 decimal places."""
        # 33.33 * 0.19 = 6.3327 -> 6.33
        result = calculate_vat(Decimal('33.33'))

        assert result['vat_amount_eur'] == Decimal('6.33')
        assert result['gross_amount_eur'] == Decimal('39.66')

    def test_calculate_vat_zero_amount(self):
        """Test VAT calculation for zero amount."""
        result = calculate_vat(Decimal('0.00'))

        assert result['vat_amount_eur'] == Decimal('0.00')
        assert result['gross_amount_eur'] == Decimal('0.00')


class TestNetFromGross:
    """Test reverse VAT calculations (gross to net)."""

    def test_calculate_net_from_gross_standard(self):
        """Test net from gross with standard 19% VAT."""
        result = calculate_net_from_gross(Decimal('119.00'))

        assert result['gross_amount_eur'] == Decimal('119.00')
        assert result['net_amount_eur'] == Decimal('100.00')
        assert result['vat_amount_eur'] == Decimal('19.00')

    def test_calculate_net_from_gross_custom_rate(self):
        """Test net from gross with custom rate."""
        result = calculate_net_from_gross(Decimal('107.00'), vat_rate=Decimal('0.07'))

        assert result['net_amount_eur'] == Decimal('100.00')
        assert result['vat_amount_eur'] == Decimal('7.00')

    def test_calculate_net_from_gross_rounding(self):
        """Test that reverse calculation handles rounding."""
        # Forward: 50.00 + 9.50 = 59.50
        result = calculate_net_from_gross(Decimal('59.50'))

        assert result['net_amount_eur'] == Decimal('50.00')


class TestVATExempt:
    """Test VAT exempt transactions."""

    def test_calculate_vat_exempt_basic(self):
        """Test VAT exempt calculation."""
        result = calculate_vat_exempt(Decimal('100.00'), "Export to non-EU country")

        assert result['net_amount_eur'] == Decimal('100.00')
        assert result['vat_rate'] == Decimal('0.00')
        assert result['vat_amount_eur'] == Decimal('0.00')
        assert result['gross_amount_eur'] == Decimal('100.00')
        assert result['exemption_reason'] == "Export to non-EU country"


class TestInvoiceVAT:
    """Test multi-line invoice VAT calculations."""

    def test_calculate_invoice_vat_single_item(self):
        """Test invoice VAT with single line item."""
        line_items = [
            {'description': 'Service A', 'net_amount_eur': 100.00}
        ]

        result = calculate_invoice_vat(line_items)

        assert result['subtotal_net_eur'] == Decimal('100')
        assert result['total_vat_eur'] == Decimal('19.00')
        assert result['total_gross_eur'] == Decimal('119.00')

    def test_calculate_invoice_vat_multiple_items(self):
        """Test invoice VAT with multiple line items."""
        line_items = [
            {'description': 'Service A', 'net_amount_eur': 50.00},
            {'description': 'Service B', 'net_amount_eur': 30.00},
            {'description': 'Service C', 'net_amount_eur': 20.00},
        ]

        result = calculate_invoice_vat(line_items)

        assert result['subtotal_net_eur'] == Decimal('100')
        assert result['total_vat_eur'] == Decimal('19.00')
        assert result['total_gross_eur'] == Decimal('119.00')

    def test_calculate_invoice_vat_breakdown(self):
        """Test that invoice includes VAT breakdown."""
        line_items = [
            {'description': 'Product', 'net_amount_eur': 100.00}
        ]

        result = calculate_invoice_vat(line_items)

        assert '19%' in result['vat_breakdown']
        assert result['vat_breakdown']['19%']['net_amount_eur'] == Decimal('100')
        assert result['vat_breakdown']['19%']['vat_amount_eur'] == Decimal('19.00')


class TestBerlinTimezone:
    """Test Berlin timezone conversion functions."""

    def test_to_berlin_timezone_from_utc(self):
        """Test converting UTC datetime to Berlin timezone."""
        utc_dt = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

        result = to_berlin_timezone(utc_dt)

        # In summer, Berlin is UTC+2
        assert result.hour == 14
        assert result.tzinfo is not None

    def test_to_berlin_timezone_from_naive(self):
        """Test converting naive datetime (assumes UTC)."""
        naive_dt = datetime(2025, 6, 15, 12, 0, 0)

        result = to_berlin_timezone(naive_dt)

        # Should assume UTC and convert to Berlin (UTC+2 in summer)
        assert result.hour == 14

    def test_from_berlin_timezone_to_utc(self):
        """Test converting Berlin datetime to UTC."""
        berlin_tz = pytz.timezone(GERMAN_TIMEZONE)
        berlin_dt = berlin_tz.localize(datetime(2025, 6, 15, 14, 0, 0))

        result = from_berlin_timezone(berlin_dt)

        # Berlin 14:00 in summer -> UTC 12:00
        assert result.hour == 12
        assert result.tzinfo == timezone.utc

    def test_to_berlin_winter_time(self):
        """Test conversion during winter (CET, UTC+1)."""
        utc_dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        result = to_berlin_timezone(utc_dt)

        # In winter, Berlin is UTC+1
        assert result.hour == 13


class TestDSTTransition:
    """Test Daylight Saving Time transition handling."""

    def test_handle_dst_no_transition(self):
        """Test handling datetime not during DST transition."""
        normal_dt = datetime(2025, 6, 15, 12, 0, 0)

        result = handle_dst_transition(normal_dt)

        assert result['transition_type'] == 'none'
        assert result['is_valid_time'] == True
        assert result['is_ambiguous_time'] == False

    def test_handle_dst_spring_forward(self):
        """Test handling spring forward transition (2 AM doesn't exist)."""
        # Last Sunday in March 2025 is March 30
        # At 2:00 AM clocks jump to 3:00 AM
        spring_forward_dt = datetime(2025, 3, 30, 2, 30, 0)

        result = handle_dst_transition(spring_forward_dt)

        assert result['transition_type'] == 'spring_forward'
        assert result['is_valid_time'] == False

    def test_handle_dst_fall_back(self):
        """Test handling fall back transition (2 AM happens twice)."""
        # Last Sunday in October 2025 is October 26
        # At 3:00 AM clocks go back to 2:00 AM
        fall_back_dt = datetime(2025, 10, 26, 2, 30, 0)

        result = handle_dst_transition(fall_back_dt)

        assert result['transition_type'] == 'fall_back'
        assert result['is_ambiguous_time'] == True


class TestBusinessHours:
    """Test business hours checking functions."""

    def test_is_business_hours_weekday_during_hours(self):
        """Test during business hours on a weekday."""
        # Monday at 10 AM Berlin time
        berlin_tz = pytz.timezone(GERMAN_TIMEZONE)
        monday_10am = berlin_tz.localize(datetime(2025, 6, 16, 10, 0, 0))  # Monday

        result = is_business_hours(monday_10am)

        assert result == True

    def test_is_business_hours_weekday_before_hours(self):
        """Test before business hours on a weekday."""
        berlin_tz = pytz.timezone(GERMAN_TIMEZONE)
        monday_7am = berlin_tz.localize(datetime(2025, 6, 16, 7, 0, 0))  # Monday

        result = is_business_hours(monday_7am)

        assert result == False

    def test_is_business_hours_weekday_after_hours(self):
        """Test after business hours on a weekday."""
        berlin_tz = pytz.timezone(GERMAN_TIMEZONE)
        monday_6pm = berlin_tz.localize(datetime(2025, 6, 16, 18, 0, 0))  # Monday

        result = is_business_hours(monday_6pm)

        assert result == False

    def test_is_business_hours_weekend(self):
        """Test on weekend (not business hours)."""
        berlin_tz = pytz.timezone(GERMAN_TIMEZONE)
        saturday_10am = berlin_tz.localize(datetime(2025, 6, 14, 10, 0, 0))  # Saturday

        result = is_business_hours(saturday_10am)

        assert result == False

    def test_is_business_hours_custom_config(self):
        """Test with custom business hours configuration."""
        berlin_tz = pytz.timezone(GERMAN_TIMEZONE)
        monday_8am = berlin_tz.localize(datetime(2025, 6, 16, 8, 0, 0))  # Monday

        custom_config = {
            'start_hour': 8,
            'end_hour': 16,
            'workdays': [0, 1, 2, 3, 4]  # Mon-Fri
        }

        result = is_business_hours(monday_8am, config=custom_config)

        assert result == True


class TestBusinessDuration:
    """Test business duration calculation functions."""

    def test_calculate_business_duration_same_day(self):
        """Test business duration within same business day."""
        berlin_tz = pytz.timezone(GERMAN_TIMEZONE)
        start = berlin_tz.localize(datetime(2025, 6, 16, 10, 0, 0))  # Monday 10 AM
        end = berlin_tz.localize(datetime(2025, 6, 16, 15, 0, 0))    # Monday 3 PM

        result = calculate_business_duration(start, end)

        assert result['total_hours'] == 5.0

    def test_calculate_business_duration_multiple_days(self):
        """Test business duration across multiple days."""
        berlin_tz = pytz.timezone(GERMAN_TIMEZONE)
        start = berlin_tz.localize(datetime(2025, 6, 16, 9, 0, 0))   # Monday 9 AM
        end = berlin_tz.localize(datetime(2025, 6, 18, 17, 0, 0))    # Wednesday 5 PM

        result = calculate_business_duration(start, end)

        # 3 full business days: 8 hours each = 24 hours
        assert result['total_hours'] >= 24.0
        assert result['business_days'] >= 3


class TestGermanDateFormatting:
    """Test German date and time formatting functions."""

    def test_format_german_date(self):
        """Test German date format (DD.MM.YYYY)."""
        dt = datetime(2025, 6, 15, 14, 30, 0)

        result = format_german_date(dt)

        assert result == "15.06.2025"

    def test_format_german_time(self):
        """Test German time format (HH:MM, 24-hour)."""
        dt = datetime(2025, 6, 15, 14, 30, 0)

        result = format_german_time(dt)

        assert result == "14:30"

    def test_format_german_time_morning(self):
        """Test German time format for morning hours."""
        dt = datetime(2025, 6, 15, 9, 5, 0)

        result = format_german_time(dt)

        assert result == "09:05"

    def test_format_german_datetime(self):
        """Test German datetime format (DD.MM.YYYY HH:MM)."""
        dt = datetime(2025, 6, 15, 14, 30, 0)

        result = format_german_datetime(dt)

        assert result == "15.06.2025 14:30"


class TestFinancialPrecision:
    """Test financial calculation precision and rounding."""

    def test_vat_precision_no_floating_point_errors(self):
        """Test that VAT calculations don't have floating point errors."""
        # Classic floating point problem: 0.1 + 0.2 != 0.3 in floats
        result = calculate_vat(Decimal('0.10'))

        # 0.10 * 0.19 = 0.019, rounds to 0.02
        assert result['vat_amount_eur'] == Decimal('0.02')

    def test_invoice_total_matches_sum(self):
        """Test that invoice total equals sum of line items + VAT."""
        line_items = [
            {'description': 'A', 'net_amount_eur': 33.33},
            {'description': 'B', 'net_amount_eur': 33.33},
            {'description': 'C', 'net_amount_eur': 33.34},
        ]

        result = calculate_invoice_vat(line_items)

        # Verify totals are consistent
        calculated_gross = result['subtotal_net_eur'] + result['total_vat_eur']
        assert result['total_gross_eur'] == calculated_gross

    def test_reverse_calculation_consistency(self):
        """Test that net->gross->net returns original value."""
        original_net = Decimal('50.00')

        # Forward: net to gross
        forward = calculate_vat(original_net)

        # Reverse: gross to net
        reverse = calculate_net_from_gross(forward['gross_amount_eur'])

        assert reverse['net_amount_eur'] == original_net


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_format_currency_very_large_amount(self):
        """Test formatting very large amounts."""
        result = format_currency(999999999.99)
        assert "999.999.999,99 EUR" == result

    def test_vat_calculation_small_amounts(self):
        """Test VAT calculation with very small amounts."""
        result = calculate_vat(Decimal('0.01'))

        # 0.01 * 0.19 = 0.0019, rounds to 0.00
        assert result['vat_amount_eur'] == Decimal('0.00')

    def test_business_hours_boundary_start(self):
        """Test exactly at business hours start."""
        berlin_tz = pytz.timezone(GERMAN_TIMEZONE)
        monday_9am = berlin_tz.localize(datetime(2025, 6, 16, 9, 0, 0))

        result = is_business_hours(monday_9am)

        assert result == True

    def test_business_hours_boundary_end(self):
        """Test exactly at business hours end."""
        berlin_tz = pytz.timezone(GERMAN_TIMEZONE)
        monday_5pm = berlin_tz.localize(datetime(2025, 6, 16, 17, 0, 0))

        result = is_business_hours(monday_5pm)

        # 17:00 is the end hour, so it's NOT within business hours
        assert result == False
