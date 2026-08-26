import re

from revo_norm.currency_utils import CURRENCY_K_SUFFIX_PATTERN, expand_currency_k_suffix
from revo_norm.num2word_ms import to_cardinal as num2word

numbers_mapping_malay = {
    "0": "kosong",
    "1": "satu",
    "2": "dua",
    "3": "tiga",
    "4": "empat",
    "5": "lima",
    "6": "enam",
    "7": "tujuh",
    "8": "lapan",
    "9": "sembilan",
}

_months = {
    "01": "Januari",
    "1": "Januari",
    "02": "Februari",
    "2": "Februari",
    "03": "Mac",
    "3": "Mac",
    "04": "April",
    "4": "April",
    "05": "Mei",
    "5": "Mei",
    "06": "Jun",
    "6": "Jun",
    "07": "Julai",
    "7": "Julai",
    "08": "Ogos",
    "8": "Ogos",
    "09": "September",
    "9": "September",
    "10": "Oktober",
    "11": "November",
    "12": "Disember",
}

# Regex
_date_re = re.compile(r"\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})\b")
_date_ymd_re = re.compile(r"\b(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})\b")

# Use shared currency K suffix pattern from currency_utils
_currency_k_re = CURRENCY_K_SUFFIX_PATTERN

_currency_re = re.compile(
    r"(?<!\w)(RM|\$|£|€|USD|EUR|GBP|MYR)(?:\s?)([\d,]+(?:[\.,]\d{1,2})?)(?:\s+(juta|bilion|trilion|ribu|million|billion|trillion|thousand))?\b",
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
    r"\b(\d{1,2})[:\.](\d{2})\s*(?:(am|pm|a\.m\.|p\.m\.|malam|petang))",
    re.IGNORECASE,
)
_time_hour_only_re = re.compile(
    r"\b(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.|malam|petang|pagi|siang|tengah hari)\b",
    re.IGNORECASE,
)
_time_no_meridian_re = re.compile(
    r"\b(\d{1,2}):(\d{2})\b(?!\s*(?:am|pm|a\.m\.|p\.m\.|malam|petang))"
    r"(?!.*%)",
    re.IGNORECASE,
)


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
        return f"{num2word(int(whole))} perpuluhan {frac_words} peratus"
    else:
        return f"{num2word(int(number))} peratus"


def normalize_time(m):
    hour, minute, meridian = m.groups()
    hour_word = num2word(int(hour))
    minute_word = num2word(int(minute))

    meridian_word = ""
    if meridian:
        meridian_word = meridian if len(meridian) > 2 else f"{meridian[0]} m"

    if minute_word == "kosong":
        return f"{hour_word} {meridian_word}".strip()
    else:
        return f"{hour_word} {minute_word} {meridian_word}".strip()


def normalize_time_hour_only(m):
    """Normalize hour-with-meridian times without minutes (jumpa 3 petang)."""
    hour, meridian = m.groups()
    hour_int = int(hour)
    meridian_lower = meridian.lower().replace(".", "")
    word_map = {
        "malam": "malam", "petang": "petang", "pagi": "pagi",
        "siang": "tengah hari", "tengah hari": "tengah hari",
    }
    if meridian_lower in word_map:
        meridian_word = word_map[meridian_lower]
    elif meridian_lower == "am":
        meridian_word = "pagi"
    else:  # pm
        meridian_word = "petang" if hour_int < 18 else "malam"
    return f"{num2word(hour_int)} {meridian_word}"


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

    if minute_word == "kosong":
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

    if symbol.upper() == "RM":
        unit_main, unit_sub = "ringgit", "sen"
    elif symbol == "$":
        unit_main, unit_sub = "dollar", "sen"
    elif symbol == "£":
        unit_main, unit_sub = "pound", "pence"
    elif symbol == "€":
        unit_main, unit_sub = "euro", "sen"
    elif symbol.upper() in ("USD", "MYR"):
        unit_main, unit_sub = "ringgit" if symbol.upper() == "MYR" else "dollar", "sen"
    else:
        unit_main, unit_sub = "unit", "subunit"

    # Normalise English magnitude words to Malay equivalents
    _mag_ms = {"million": "juta", "billion": "bilion", "trillion": "trilion", "thousand": "ribu"}
    if magnitude in _mag_ms:
        magnitude = _mag_ms[magnitude]

    if magnitude:
        if "." in amount:
            whole, frac = amount.split(".")
            frac_words = " ".join(num2word(int(d)) for d in frac)
            return f"{num2word(int(whole))} perpuluhan {frac_words} {magnitude} {unit_main}"
        else:
            return f"{num2word(int(amount))} {magnitude} {unit_main}"

    if "." in amount:
        ringgit, sen = amount.split(".")
        if sen != "00":
            return f"{num2word(int(ringgit))} {unit_main} {num2word(int(sen[:2]))} {unit_sub}"
        else:
            return f"{num2word(int(ringgit))} {unit_main}"
    else:
        return f"{num2word(int(amount))} {unit_main}"


def normalize_decimal(m):
    whole, frac = m.group(1), m.group(2)
    # Handle multi-digit decimals by speaking each digit
    frac_words = " ".join(num2word(int(digit)) for digit in frac)
    return f"{num2word(int(whole))} perpuluhan {frac_words}"


def normalize_number_with_commas(m):
    """Normalize numbers with commas like 1,000,000 or 7,832."""
    num_str = m.group(0).replace(",", "")
    num = int(num_str)
    return num2word(num)


def normalize_dashed_digits(m):
    raw = m.group(1)
    return " ".join(numbers_mapping_malay.get(ch, ch) for ch in raw if ch in numbers_mapping_malay)


def normalize_mixed_alnum(m):
    token = m.group(0)
    if is_only_digits_and_dashes(token):
        return token
    if is_mixed_alnum(token):
        # Handle tokens like v2.3.1 - split on dots and process each part
        if "." in token and not re.match(r"^[A-Za-z]", token):
            # Handle cases like 2.3.1 (starts with digit)
            return " ".join(
                numbers_mapping_malay.get(ch, ch.upper()) for ch in token if ch.isalnum()
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
                            numbers_mapping_malay.get(ch, ch.upper()) for ch in part if ch.isalnum()
                        )
                    )
                if i < len(parts) - 1:  # Add "perpuluhan" between parts
                    result.append("perpuluhan")
            return " ".join(result)
        else:
            return " ".join(
                numbers_mapping_malay.get(ch, ch.upper()) for ch in token if ch.isalnum()
            )
    return token


def normalize_number(m):
    if len(m.group(0)) > 4:
        return " ".join(num2word(int(digit)) for digit in m.group(0))
    else:
        return num2word(int(m.group(0)))


def normalize_malay(text: str) -> str:
    """
    Main Malay text normalization function.

    Entity-aware approach: Detects and normalizes specific entities
    (currency, dates, times, etc.) rather than processing the whole text.

    Currency K-suffix (RM30K) is expanded to full numbers (RM30000)
    BEFORE main currency normalization.
    """
    # Step 1: Expand currency with K suffix (entity-aware preprocessing)
    # e.g., RM30K → RM30000, RM1.5K → RM1500
    text = re.sub(_currency_k_re, expand_currency_k_suffix, text)

    # Step 2: Process other entities
    text = re.sub(_date_ymd_re, normalize_date_ymd, text)
    text = re.sub(_date_re, normalize_date, text)
    text = re.sub(_currency_re, normalize_currency, text)
    text = re.sub(_time_hour_only_re, normalize_time_hour_only, text)
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
