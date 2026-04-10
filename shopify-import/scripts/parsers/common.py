"""Shared utilities for platform CSV parsers."""

import csv
import re


def read_csv(path):
    """Read a CSV file and return a list of row dicts.

    Handles BOM markers (utf-8-sig) and strips whitespace from header names.
    """
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        # Strip whitespace from headers (some exports pad them)
        if reader.fieldnames:
            reader.fieldnames = [name.strip() for name in reader.fieldnames]
        return list(reader)


def safe_float(value, default=0):
    """Parse a string to float, returning default on failure.

    Negative values are clamped to 0 for prices (Shopify rejects negative prices).
    Use safe_float_signed() when negatives are valid (e.g. inventory adjustments).
    """
    if not value or not str(value).strip():
        return default
    try:
        result = float(value)
        return max(result, 0)
    except (ValueError, TypeError):
        return default


def safe_float_signed(value, default=0):
    """Parse a string to float, allowing negative values."""
    if not value or not str(value).strip():
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Parse a string to int (via float for '10.0' style), returning default on failure."""
    if not value or not str(value).strip():
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def parse_weight_column(col_name, value):
    """Extract weight value and unit from a column header like 'Weight (kg)'.

    Returns (float, str) or (None, None) on failure.
    """
    if not col_name:
        return None, None
    m = re.match(r"Weight\s*\((\w+)\)", col_name)
    if not m:
        return None, None
    weight = safe_float(value)
    if weight is None or weight == 0:
        return None, None
    unit_map = {"kg": "KILOGRAMS", "g": "GRAMS", "lb": "POUNDS", "lbs": "POUNDS", "oz": "OUNCES"}
    return weight, unit_map.get(m.group(1).lower(), "KILOGRAMS")


def parse_gmc_price(s):
    """Parse Google Merchant Center price format like '29.99 USD' → 29.99.

    Returns 0 on failure (empty, 'FREE', malformed, etc.).
    """
    if not s or not s.strip():
        return 0
    # Strip currency codes and symbols, keep digits and decimal point
    numeric = re.sub(r"[^\d.]", "", s.split()[0])
    if not numeric:
        return 0
    try:
        return float(numeric)
    except ValueError:
        return 0


def parse_gmc_weight(s):
    """Parse GMC weight format like '0.5 kg' → (0.5, 'KILOGRAMS').

    Returns (None, None) on failure.
    """
    if not s or not s.strip():
        return None, None
    parts = s.strip().split()
    val = safe_float(parts[0])
    if not val:
        return None, None
    unit_map = {"kg": "KILOGRAMS", "g": "GRAMS", "lb": "POUNDS", "oz": "OUNCES"}
    unit = unit_map.get(parts[1].lower(), "KILOGRAMS") if len(parts) > 1 else "KILOGRAMS"
    return val, unit

