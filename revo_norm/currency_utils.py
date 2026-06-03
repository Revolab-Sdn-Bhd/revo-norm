"""
Shared utility functions for currency normalization across languages.

These functions are language-agnostic and can be used by both
English and Malay normalizers.
"""

import re


def expand_currency_k_suffix(m):
    """
    Expand currency with 'K' suffix (thousands) to full number.
    This is entity-aware: only processes detected currency entities.

    This is a universal function that works across all languages.

    Examples:
        RM30K -> RM30000
        RM70K -> RM70000
        RM1.5K -> RM1500
        $50K -> $50000
        EUR100K -> EUR100000
    """
    symbol = m.group(1)  # RM, $, etc.
    amount = m.group(2)  # e.g., "30", "1.5"

    # Convert to float and multiply by 1000
    amount_float = float(amount) * 1000

    # Convert to integer if it's a whole number
    amount_final = int(amount_float) if amount_float == int(amount_float) else amount_float

    return f"{symbol}{amount_final}"


def expand_currency_m_suffix(m):
    """
    Expand currency with 'M' suffix (millions) to full number.

    Examples:
        RM19m  -> RM19000000
        $5M    -> $5000000
        RM1.5M -> RM1500000
    """
    symbol = m.group(1)
    amount = m.group(2)
    amount_float = float(amount) * 1_000_000
    amount_final = int(amount_float) if amount_float == int(amount_float) else amount_float
    return f"{symbol}{amount_final}"


def expand_currency_b_suffix(m):
    """
    Expand currency with 'B' suffix (billions) to full number.

    Examples:
        RM1B   -> RM1000000000
        $2.5B  -> $2500000000
    """
    symbol = m.group(1)
    amount = m.group(2)
    amount_float = float(amount) * 1_000_000_000
    amount_final = int(amount_float) if amount_float == int(amount_float) else amount_float
    return f"{symbol}{amount_final}"


def expand_currency_t_suffix(m):
    """
    Expand currency with 'T' suffix (trillions) to full number.

    Examples:
        RM1T -> RM1000000000000
        $2T  -> $2000000000000
    """
    symbol = m.group(1)
    amount = m.group(2)
    amount_float = float(amount) * 1_000_000_000_000
    amount_final = int(amount_float) if amount_float == int(amount_float) else amount_float
    return f"{symbol}{amount_final}"


# Regex pattern for currency with K suffix (thousands)
# Uses (?<!\w) instead of \b to handle symbols like $ that aren't word characters
# This is a universal pattern that works across all languages
CURRENCY_K_SUFFIX_PATTERN = re.compile(
    r"(?<!\w)(RM|\$|£|€|USD|EUR|GBP|MYR)(?:\s?)(\d+(?:\.\d+)?)K\b", re.IGNORECASE
)

# Regex pattern for currency with M suffix (millions)
CURRENCY_M_SUFFIX_PATTERN = re.compile(
    r"(?<!\w)(RM|\$|£|€|USD|EUR|GBP|MYR)(?:\s?)(\d+(?:\.\d+)?)M\b", re.IGNORECASE
)

# Regex pattern for currency with B suffix (billions)
CURRENCY_B_SUFFIX_PATTERN = re.compile(
    r"(?<!\w)(RM|\$|£|€|USD|EUR|GBP|MYR)(?:\s?)(\d+(?:\.\d+)?)B\b", re.IGNORECASE
)

# Regex pattern for currency with T suffix (trillions)
CURRENCY_T_SUFFIX_PATTERN = re.compile(
    r"(?<!\w)(RM|\$|£|€|USD|EUR|GBP|MYR)(?:\s?)(\d+(?:\.\d+)?)T\b", re.IGNORECASE
)

# Malay currency word suffixes
CURRENCY_RIBU_PATTERN = re.compile(
    r"(?<!\w)(RM|\$|£|€|USD|EUR|GBP|MYR)(?:\s?)(\d+(?:\.\d+)?)\s+ribu\b", re.IGNORECASE
)
CURRENCY_JUTA_PATTERN = re.compile(
    r"(?<!\w)(RM|\$|£|€|USD|EUR|GBP|MYR)(?:\s?)(\d+(?:\.\d+)?)\s+juta\b", re.IGNORECASE
)
CURRENCY_MILIAR_PATTERN = re.compile(
    r"(?<!\w)(RM|\$|£|€|USD|EUR|GBP|MYR)(?:\s?)(\d+(?:\.\d+)?)\s+miliar\b", re.IGNORECASE
)
CURRENCY_TRILION_PATTERN = re.compile(
    r"(?<!\w)(RM|\$|£|€|USD|EUR|GBP|MYR)(?:\s?)(\d+(?:\.\d+)?)\s+trilion\b", re.IGNORECASE
)
