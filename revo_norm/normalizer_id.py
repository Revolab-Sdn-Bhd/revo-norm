"""Indonesian text normalization for TTS.

Handles currency (Rp), dates, times, numbers, percentages, and mixed alnum tokens.
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

_date_re = re.compile(r"\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})\b")
_date_ymd_re = re.compile(r"\b(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})\b")

_currency_k_re = CURRENCY_K_SUFFIX_PATTERN

_currency_re = re.compile(
    r"(?<!\w)(Rp|rp)(?:\s?)([\d,]+(?:[\.,]\d{1,2})?)(?:\s+(juta|miliar|triliun|ribu|million|billion|trillion|thousand))?\b"
    r"|(?:\b)(USD|EUR|GBP|\$|€|£)(?:\s?)([\d,]+(?:[\.,]\d{1,2})?)(?:\s+(juta|miliar|triliun|ribu|million|billion|trillion|thousand))?\b",
    re.IGNORECASE,
)
# Rp with Indonesian-style dotted thousand separators: Rp12.500.000, Rp1.000.000.000
_rp_dotted_re = re.compile(
    r"(?<!\w)(Rp|rp)\.?\s?(\d{1,3}(?:\.\d{3})+)(?:\s+(juta|miliar|triliun|ribu))?\b",
    re.IGNORECASE,
)
_decimal_re = re.compile(r"\b(\d+),(\d+)\b")
_dashed_digit_re = re.compile(r"(?<![A-Za-z])([+\d]+(?:-[\d]+)+)(?![A-Za-z])")
_alnum_re = re.compile(r"\b[\w\-]+\b")
_number_re = re.compile(r"\b\d+\b")
_number_with_dots_re = re.compile(r"(?:Rp\.?\s?)?(\d{1,3}(?:\.\d{3})+)")
_percentage_re = re.compile(r"\b(\d+(?:[,.]\d+)?)%")
_time_re = re.compile(
    r"\b(\d{1,2})[:\.](\d{2})\s*(?:(pagi|siang|sore|malam|am|pm|a\.m\.|p\.m\.))",
    re.IGNORECASE,
)
_time_no_meridian_re = re.compile(
    r"\b(\d{1,2})[:\.](\d{2})\b(?!\s*(?:pagi|siang|sore|malam|am|pm|a\.m\.|p\.m\.))"
    r"(?!.*%)",
    re.IGNORECASE,
)


def is_mixed_alnum(token):
    return any(c.isalpha() for c in token) and any(c.isdigit() for c in token)


def is_only_digits_and_dashes(token):
    return all(c.isdigit() or c in "+-" for c in token.replace("-", ""))


def normalize_percentage(m):
    number = m.group(1).replace(",", ".")
    if "." in number:
        whole, frac = number.split(".")
        frac_words = " ".join(num2word(int(digit)) for digit in frac)
        return f"{num2word(int(whole))} koma {frac_words} persen"
    else:
        return f"{num2word(int(number))} persen"


def normalize_rp_dotted(m):
    """Normalize Rp with dotted thousand separators: Rp12.500.000 → dua belas juta lima ratus ribu rupiah."""
    symbol, amount, magnitude = m.groups()
    num_str = amount.replace(".", "")
    magnitude = (magnitude or "").lower() or None

    if magnitude:
        return f"{num2word(int(num_str))} {magnitude} rupiah"
    return f"{num2word(int(num_str))} rupiah"


def normalize_time(m):
    hour, minute, meridian = m.groups()
    hour_int = int(hour)
    minute_int = int(minute)
    hour_word = num2word(hour_int)
    minute_word = num2word(minute_int)

    meridian_lower = (meridian or "").lower()
    meridian_word = ""
    if meridian_lower in ("pagi", "siang", "sore", "malam"):
        meridian_word = meridian_lower
    elif meridian_lower in ("am", "a.m."):
        meridian_word = "pagi"
    elif meridian_lower in ("pm", "p.m."):
        meridian_word = "sore" if hour_int < 18 else "malam"

    if minute_int == 0:
        return f"{hour_word} {meridian_word}".strip()
    else:
        return f"{hour_word} {minute_word} {meridian_word}".strip()


def normalize_time_no_meridian(m):
    hour, minute = m.groups()
    hour_int = int(hour)
    minute_int = int(minute)

    if hour_int == 0 and minute_int == 0:
        return "tengah malam"
    if hour_int == 12 and minute_int == 0:
        return "tengah hari"

    hour_word = num2word(hour_int)
    minute_word = num2word(minute_int)

    if minute_int == 0:
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
    groups = m.groups()
    # Rp format: groups 1-3
    if groups[0]:
        symbol = groups[0]
        amount = groups[1].replace(".", "").replace(",", ".")
        magnitude = (groups[2] or "").lower() or None
        unit_main = "rupiah"
    # Foreign currency: groups 4-6
    else:
        symbol = groups[3]
        amount = groups[4].replace(".", "").replace(",", ".")
        magnitude = (groups[5] or "").lower() or None
        if symbol.upper() in ("USD", "$"):
            unit_main = "dolar"
        elif symbol == "€":
            unit_main = "euro"
        elif symbol == "£":
            unit_main = "pound"
        elif symbol.upper() == "GBP":
            unit_main = "pound sterling"
        else:
            unit_main = "dolar"

    _mag_id = {"million": "juta", "billion": "miliar", "trillion": "triliun", "thousand": "ribu"}
    if magnitude in _mag_id:
        magnitude = _mag_id[magnitude]

    if magnitude:
        if "." in amount:
            whole, frac = amount.split(".")
            frac_words = " ".join(num2word(int(d)) for d in frac)
            return f"{num2word(int(whole))} koma {frac_words} {magnitude} {unit_main}"
        else:
            return f"{num2word(int(amount))} {magnitude} {unit_main}"

    if "." in amount:
        main, sub = amount.split(".")
        if sub != "00":
            return f"{num2word(int(main))} {unit_main} {num2word(int(sub[:2]))} sen"
        else:
            return f"{num2word(int(main))} {unit_main}"
    else:
        return f"{num2word(int(amount))} {unit_main}"


def normalize_decimal(m):
    whole, frac = m.group(1), m.group(2)
    frac_words = " ".join(num2word(int(digit)) for digit in frac)
    return f"{num2word(int(whole))} koma {frac_words}"


def normalize_number_with_dots(m):
    """Normalize Indonesian-style dotted numbers like 12.500.000."""
    num_str = m.group(1).replace(".", "")
    num = int(num_str)
    return num2word(num)


def normalize_dashed_digits(m):
    raw = m.group(1)
    return " ".join(numbers_mapping_indonesian.get(ch, ch) for ch in raw if ch in numbers_mapping_indonesian)


def normalize_number(m):
    if len(m.group(0)) > 4:
        return " ".join(num2word(int(digit)) for digit in m.group(0))
    else:
        return num2word(int(m.group(0)))


def normalize_mixed_alnum(m):
    token = m.group(0)
    if is_only_digits_and_dashes(token):
        return token
    if is_mixed_alnum(token):
        if "." in token and not re.match(r"^[A-Za-z]", token):
            return " ".join(
                numbers_mapping_indonesian.get(ch, ch.upper()) for ch in token if ch.isalnum()
            )
        elif "." in token:
            parts = token.split(".")
            result = []
            for i, part in enumerate(parts):
                if part.isalpha():
                    result.append(part.upper())
                elif part.isdigit():
                    result.append(num2word(int(part)))
                elif part:
                    result.append(
                        " ".join(
                            numbers_mapping_indonesian.get(ch, ch.upper()) for ch in part if ch.isalnum()
                        )
                    )
                if i < len(parts) - 1:
                    result.append("koma")
            return " ".join(result)
        else:
            return " ".join(
                numbers_mapping_indonesian.get(ch, ch.upper()) for ch in token if ch.isalnum()
            )
    return token


def normalize_indonesian(text: str) -> str:
    """Main Indonesian text normalization function."""
    text = re.sub(_currency_k_re, expand_currency_k_suffix, text)
    text = re.sub(_rp_dotted_re, normalize_rp_dotted, text)
    text = re.sub(_date_ymd_re, normalize_date_ymd, text)
    text = re.sub(_date_re, normalize_date, text)
    text = re.sub(_currency_re, normalize_currency, text)
    text = re.sub(_time_no_meridian_re, normalize_time_no_meridian, text)
    text = re.sub(_time_re, normalize_time, text)
    text = re.sub(_percentage_re, normalize_percentage, text)
    text = re.sub(_decimal_re, normalize_decimal, text)
    text = re.sub(_dashed_digit_re, normalize_dashed_digits, text)
    text = re.sub(_number_with_dots_re, normalize_number_with_dots, text)
    text = re.sub(_number_re, normalize_number, text)
    text = re.sub(_alnum_re, normalize_mixed_alnum, text)
    return text
