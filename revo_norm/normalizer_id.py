"""Indonesian text normalization for TTS.

Covers Indonesian vocabulary (delapan/nol, koma, persen, Maret/Agustus,
Rp/rupiah) and written number conventions: dots as thousands separators
(1.000.000), comma as decimal separator (10,5), and colloquial currency
suffixes (Rp5rb, Rp5jt, Rp5M where M = miliar, not million).
"""

import re

from revo_norm.currency_utils import CURRENCY_K_SUFFIX_PATTERN, expand_currency_k_suffix
from revo_norm.num2word_id import to_cardinal as num2word

numbers_mapping_indonesian = {
    "0": "nol",
    "1": "satu",
    "2": "dua",
    "3": "tiga",
    "4": "empat",
    "5": "lima",
    "6": "enam",
    "7": "tujuh",
    "8": "delapan",
    "9": "sembilan",
}

_months = {
    "01": "Januari",
    "1": "Januari",
    "02": "Februari",
    "2": "Februari",
    "03": "Maret",
    "3": "Maret",
    "04": "April",
    "4": "April",
    "05": "Mei",
    "5": "Mei",
    "06": "Juni",
    "6": "Juni",
    "07": "Juli",
    "7": "Juli",
    "08": "Agustus",
    "8": "Agustus",
    "09": "September",
    "9": "September",
    "10": "Oktober",
    "11": "November",
    "12": "Desember",
}

# --- Indonesian written number conventions -------------------------------
# 1.000.000 → 1,000,000 and 10.000,50 → 10,000.50 (dots as thousands
# separators, comma as decimal separator) — the comma-grouped form is what
# the rest of the pipeline reads as a formatted cardinal. The lookarounds
# reject IP addresses (192.168.1.1) and version strings (1.000.5).
_DOTTED_THOUSANDS_RE = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{3})+)(?:,(\d{1,2}))?(?!\.?\d)")
# 10,5 → 10.5 (comma as decimal separator, 1-2 digits; 3+ digits = grouping)
_COMMA_DECIMAL_RE = re.compile(r"(?<![\d.,])(\d+),(\d{1,2})(?![\d.,])")
# Colloquial currency suffixes on rupiah amounts. In Indonesian money slang
# M = miliar (1e9, NOT million) and T = triliun.
_ID_CURRENCY_SUFFIX_RE = re.compile(
    r"(?<!\w)((?:Rp|IDR)\s?\d+(?:\.\d+)?)\s*(rb|jt|K|M|B|T)\b", re.IGNORECASE
)
_ID_SUFFIX_WORDS = {
    "rb": "ribu",
    "jt": "juta",
    "k": "ribu",
    "m": "miliar",
    "b": "miliar",
    "t": "triliun",
}
# Bare rb/jt suffixes are unambiguous even without a currency symbol (5jt)
_ID_BARE_SUFFIX_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*(rb|jt)\b", re.IGNORECASE)


def _dotted_to_comma_grouped(m: re.Match) -> str:
    # With a decimal tail, plain digits + dot decimal parse best downstream
    # (10.000,50 → 10000.50); integers keep grouping so they read as
    # formatted cardinals, not digit-by-digit (1.000.000 → 1,000,000).
    if m.group(2):
        return f"{m.group(1).replace('.', '')}.{m.group(2)}"
    return m.group(1).replace(".", ",")


def preparse_number_formats(text: str) -> str:
    """Rewrite Indonesian written number conventions into the plain digit
    forms the rest of the pipeline expects. Idempotent."""
    text = _DOTTED_THOUSANDS_RE.sub(_dotted_to_comma_grouped, text)
    text = _COMMA_DECIMAL_RE.sub(r"\1.\2", text)
    text = _ID_CURRENCY_SUFFIX_RE.sub(
        lambda m: f"{m.group(1)} {_ID_SUFFIX_WORDS[m.group(2).lower()]}", text
    )
    text = _ID_BARE_SUFFIX_RE.sub(
        lambda m: f"{m.group(1)} {_ID_SUFFIX_WORDS[m.group(2).lower()]}", text
    )
    return text


# Regex
_date_re = re.compile(r"\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})\b")
_date_ymd_re = re.compile(r"\b(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})\b")

# Use shared currency K suffix pattern from currency_utils
_currency_k_re = CURRENCY_K_SUFFIX_PATTERN

_currency_re = re.compile(
    r"(?<!\w)(Rp|IDR|RM|\$|£|€|USD|EUR|GBP|MYR)(?:\s?)([\d,]+(?:[\.,]\d{1,2})?)"
    r"(?:\s+(juta|miliar|triliun|ribu|million|billion|trillion|thousand))?\b",
    re.IGNORECASE,
)
_decimal_re = re.compile(r"\b(\d+)\.(\d+)\b")
_dashed_digit_re = re.compile(r"(?<![A-Za-z])([+\d]+(?:-[\d]+)+)(?![A-Za-z])")
_alnum_re = re.compile(r"\b[\w\-]+\b")
_number_re = re.compile(r"\b\d+\b")
_number_with_commas_re = re.compile(r"\b\d{1,3}(?:,\d{3})+\b")
_adjacent_digit_groups_re = re.compile(r"(?<!\S)(\d+(?:\s+\d+)+)(?=[\s.,!?]|$)")
_percentage_re = re.compile(r"\b(\d+(?:\.\d+)?)%")
_time_re = re.compile(
    r"\b(\d{1,2})[:\.](\d{2})\s*(?:(am|pm|a\.m\.|p\.m\.|pagi|siang|sore|malam))",
    re.IGNORECASE,
)
_time_no_meridian_re = re.compile(
    r"\b(\d{1,2}):(\d{2})\b(?!\s*(?:am|pm|a\.m\.|p\.m\.|pagi|siang|sore|malam))"
    r"(?!.*%)",
    re.IGNORECASE,
)

_CURRENCY_UNITS = {
    "RP": ("rupiah", "sen"),
    "IDR": ("rupiah", "sen"),
    "RM": ("ringgit", "sen"),
    "MYR": ("ringgit", "sen"),
    "$": ("dolar", "sen"),
    "USD": ("dolar", "sen"),
    "£": ("pound", "pence"),
    "GBP": ("pound", "pence"),
    "€": ("euro", "sen"),
    "EUR": ("euro", "sen"),
}

# Normalise English magnitude words to Indonesian equivalents
_MAG_ID = {"million": "juta", "billion": "miliar", "trillion": "triliun", "thousand": "ribu"}


def is_mixed_alnum(token):
    return any(c.isalpha() for c in token) and any(c.isdigit() for c in token)


def is_only_digits_and_dashes(token):
    return all(c.isdigit() or c in "+-" for c in token.replace("-", ""))


def normalize_percentage(m):
    number = m.group(1)
    if "." in number:
        whole, frac = number.split(".")
        # Handle multi-digit decimals by speaking each digit
        frac_words = " ".join(num2word(int(digit)) for digit in frac)
        return f"{num2word(int(whole))} koma {frac_words} persen"
    else:
        return f"{num2word(int(number))} persen"


def normalize_time(m):
    hour, minute, meridian = m.groups()
    hour_word = num2word(int(hour))
    minute_word = num2word(int(minute))

    meridian_word = ""
    if meridian:
        meridian_word = meridian if len(meridian) > 2 else f"{meridian[0]} m"

    if minute_word == "nol":
        return f"{hour_word} {meridian_word}".strip()
    else:
        return f"{hour_word} {minute_word} {meridian_word}".strip()


def normalize_time_no_meridian(m):
    """Normalize time without meridian (e.g., 17:30, 09:00)."""
    hour, minute = m.groups()
    hour_int = int(hour)
    minute_int = int(minute)

    # Special case for midnight (00:00)
    if hour_int == 0 and minute_int == 0:
        return "tengah malam"
    # Special case for noon (12:00)
    if hour_int == 12 and minute_int == 0:
        return "tengah hari"

    hour_word = num2word(hour_int)
    minute_word = num2word(minute_int)

    if minute_word == "nol":
        return hour_word
    else:
        return f"{hour_word} {minute_word}"


def normalize_date(m):
    day, month, year = m.groups()
    month_name = _months.get(month.lstrip("0"), month)
    return f"{num2word(int(day))} {month_name} {num2word(int(year))}"


def normalize_date_ymd(m):
    year, month, day = m.groups()
    month_name = _months.get(month.lstrip("0"), month)
    return f"{num2word(int(day))} {month_name} {num2word(int(year))}"


def normalize_currency(m):
    symbol = m.group(1)
    amount = m.group(2).replace(",", "")
    magnitude = (m.group(3) or "").lower() or None

    unit_main, unit_sub = _CURRENCY_UNITS.get(symbol.upper(), ("unit", "subunit"))

    if magnitude in _MAG_ID:
        magnitude = _MAG_ID[magnitude]

    if magnitude:
        if "." in amount:
            whole, frac = amount.split(".")
            frac_words = " ".join(num2word(int(d)) for d in frac)
            return f"{num2word(int(whole))} koma {frac_words} {magnitude} {unit_main}"
        else:
            return f"{num2word(int(amount))} {magnitude} {unit_main}"

    if "." in amount:
        rupiah, sen = amount.split(".")
        if sen != "00":
            return f"{num2word(int(rupiah))} {unit_main} {num2word(int(sen[:2]))} {unit_sub}"
        else:
            return f"{num2word(int(rupiah))} {unit_main}"
    else:
        return f"{num2word(int(amount))} {unit_main}"


def normalize_decimal(m):
    whole, frac = m.group(1), m.group(2)
    # Handle multi-digit decimals by speaking each digit
    frac_words = " ".join(num2word(int(digit)) for digit in frac)
    return f"{num2word(int(whole))} koma {frac_words}"


def normalize_number_with_commas(m):
    """Normalize numbers with commas like 1,000,000 or 7,832."""
    num_str = m.group(0).replace(",", "")
    return num2word(int(num_str))


def normalize_dashed_digits(m):
    raw = m.group(1)
    return " ".join(
        numbers_mapping_indonesian.get(ch, ch) for ch in raw if ch in numbers_mapping_indonesian
    )


def normalize_mixed_alnum(m):
    token = m.group(0)
    if is_only_digits_and_dashes(token):
        return token
    if is_mixed_alnum(token):
        # Handle tokens like v2.3.1 - split on dots and process each part
        if "." in token and not re.match(r"^[A-Za-z]", token):
            # Handle cases like 2.3.1 (starts with digit)
            return " ".join(
                numbers_mapping_indonesian.get(ch, ch.upper()) for ch in token if ch.isalnum()
            )
        elif "." in token:
            # Handle cases like v2.3.1 (starts with letter)
            parts = token.split(".")
            result = []
            for i, part in enumerate(parts):
                if part.isalpha():
                    result.append(part.upper())
                elif part.isdigit():
                    result.append(num2word(int(part)))
                elif part:  # mixed alnum like INV
                    result.append(
                        " ".join(
                            numbers_mapping_indonesian.get(ch, ch.upper())
                            for ch in part
                            if ch.isalnum()
                        )
                    )
                if i < len(parts) - 1:  # Add "koma" between parts
                    result.append("koma")
            return " ".join(result)
        else:
            return " ".join(
                numbers_mapping_indonesian.get(ch, ch.upper()) for ch in token if ch.isalnum()
            )
    return token


def normalize_number(m):
    if len(m.group(0)) > 4:
        return " ".join(num2word(int(digit)) for digit in m.group(0))
    else:
        return num2word(int(m.group(0)))


def normalize_indonesian(text: str) -> str:
    """
    Main Indonesian text normalization function.

    Entity-aware approach: detects and normalizes specific entities
    (currency, dates, times, etc.), preceded by a rewrite of Indonesian
    written number conventions (dotted thousands, comma decimals,
    rupiah suffixes) into plain digit forms.
    """
    # Step 0: Indonesian number-format conventions → plain digits
    text = preparse_number_formats(text)

    # Step 1: Expand currency with K suffix (entity-aware preprocessing)
    text = re.sub(_currency_k_re, expand_currency_k_suffix, text)

    # Step 2: Process other entities
    text = re.sub(_date_ymd_re, normalize_date_ymd, text)
    text = re.sub(_date_re, normalize_date, text)
    text = re.sub(_currency_re, normalize_currency, text)
    text = re.sub(_time_no_meridian_re, normalize_time_no_meridian, text)
    text = re.sub(_time_re, normalize_time, text)
    text = re.sub(_percentage_re, normalize_percentage, text)
    text = re.sub(_decimal_re, normalize_decimal, text)
    text = re.sub(_dashed_digit_re, normalize_dashed_digits, text)
    text = re.sub(_number_with_commas_re, normalize_number_with_commas, text)
    # Combine adjacent digit groups (e.g. "1111 222222 5555555" → "11112222225555555")
    text = re.sub(_adjacent_digit_groups_re, lambda m: m.group(0).replace(" ", ""), text)
    text = re.sub(_number_re, normalize_number, text)
    text = re.sub(_alnum_re, normalize_mixed_alnum, text)
    return text
