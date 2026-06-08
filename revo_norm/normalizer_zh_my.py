"""
Malaysian Chinese text normalization for TTS.

Extends standard Chinese with:
- Code-mixing support (CJK + Latin script in same sentence)
- Colloquial currency ($ → 块 instead of 美元)

Dates, times, currency, temperature, and measurements are handled by
entity extraction and shared_features (which respect config flags).
"""

import re

from revo_norm.normalizer_zh import (
    _MONTHS,
    _alnum_re,
    _currency_re,
    _dashed_alnum_re,
    _dashed_digit_re,
    _date_dmy_re,
    _date_ymd_re,
    _decimal_re,
    _leftover_dot_re,
    _measurement_re,
    _number_re,
    _number_with_commas_re,
    _percentage_re,
    _temperature_re,
    _time_no_meridian_re,
    _time_re,
    _time_shortform_re,
    _time_zh_re,
    normalize_alnum,
    normalize_dashed_alnum,
    normalize_dashed_digits,
    normalize_decimal,
    normalize_leftover_dot,
    normalize_measurement,
    normalize_number,
    normalize_number_with_commas,
    normalize_temperature_zh,
)
from revo_norm.num2word_zh import to_cardinal, to_year

# Times
_TIMES = {
    "am": "早上",
    "pm": "下午"
}

# CJK unified ideographs range — used for code-mixing detection
_CJK_RE = re.compile(r"[一-鿿㐀-䶿]")
_LATIN_RE = re.compile(r"[A-Za-z]")


def _has_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text))


def _has_latin(text: str) -> bool:
    return bool(_LATIN_RE.search(text))


def normalize_percentage(m: re.Match) -> str:
    number = m.group(1)
    if "." in number:
        whole, frac = number.split(".")
        frac_words = "".join(to_cardinal(int(d)) for d in frac)
        return f"{to_cardinal(int(whole))}点{frac_words}巴仙"
    return f"{to_cardinal(int(float(number)))}巴仙"


def normalize_date_dmy(m: re.Match) -> str:
    day, month, year = m.groups()
    if int(month) > 12 and int(day) <= 12:
        month, day = day, month

    month_str = _MONTHS.get(month, month)
    return f"{to_year(int(year))}年{month_str}月{to_cardinal(int(day))}号"


def normalize_date_ymd(m: re.Match) -> str:
    year, month, day = m.groups()
    month_str = _MONTHS.get(month, month)
    return f"{to_year(int(year))}年{month_str}月{to_cardinal(int(day))}号"


def normalize_currency(m: re.Match) -> str:
    symbol = m.group(1).upper()
    amount = m.group(2).replace(",", "")
    magnitude = m.group(3) or ""

    if symbol.upper() in ("RM", "MYR"):
        unit_main, unit_sub = "令吉", "仙"
    elif symbol in ("$", "USD"):
        unit_main, unit_sub = "块", "仙"
    elif symbol in ("£", "GBP"):
        unit_main, unit_sub = "英磅", "仙"
    elif symbol in ("€", "EUR"):
        unit_main, unit_sub = "欧元", "仙"
    else:
        unit_main, unit_sub = "块", "仙"

    if "." in amount:
        whole, frac = amount.split(".")
        frac = frac.ljust(2, "0")[:2]
        if frac != "00":
            return f"{to_cardinal(int(whole))}{magnitude}{unit_main}{to_cardinal(int(frac))}{unit_sub}"
        else:
            return f"{to_cardinal(int(whole))}{magnitude}{unit_main}"

    return f"{to_cardinal(int(amount))}{magnitude}{unit_main}"


def normalize_time(m):
    hour, minute, meridian = m.groups()
    hour_word = to_cardinal(int(hour))
    minute_word = to_cardinal(int(minute))

    meridian_word = ""
    if meridian:
        meridian_word = f"{meridian[0]}m"

    if minute_word == "零":
        return f"{_TIMES[meridian_word.lower()]}{hour_word}点"
    else:
        return f"{_TIMES[meridian_word.lower()]}{hour_word}点{minute_word}分"


def normalize_time_zh(m):
    meridian, hour, minute = m.groups()
    hour_word = to_cardinal(int(hour))
    minute_word = to_cardinal(int(minute))

    if minute_word == "零":
        return f"{meridian}{hour_word}点"
    else:
        return f"{meridian}{hour_word}点{minute_word}分"


def normalize_time_no_meridian(m):
    hour, minute = m.groups()
    hour_int = int(hour)
    minute_int = int(minute)

    # Special case for midnight (00:00)
    if hour_int == 0 and minute_int == 0:
        return "半夜十二点"
    # Special case for noon (12:00)
    if hour_int == 12 and minute_int == 0:
        return "中午十二点"

    hour_word = to_cardinal(hour_int)
    minute_word = to_cardinal(minute_int)

    if minute_word == "零":
        return f"{hour_word}点"
    else:
        return f"{hour_word}点{minute_word}分"


def normalize_time_shortform(m):
    hour, meridian = m.groups()
    hour_word = to_cardinal(int(hour))
    meridian_word = ""
    if meridian:
        meridian_word = f"{meridian[0]}m"
        return f"{_TIMES[meridian_word.lower()]}{hour_word}点"


def text_normalize_zh_my(text: str) -> str:
    """Main Malaysian Chinese text normalization function."""
    text = re.sub(_percentage_re, normalize_percentage, text)
    text = re.sub(_date_dmy_re, normalize_date_dmy, text)
    text = re.sub(_date_ymd_re, normalize_date_ymd, text)
    text = re.sub(_measurement_re, normalize_measurement, text)
    text = re.sub(_currency_re, normalize_currency, text)
    text = re.sub(_time_no_meridian_re, normalize_time_no_meridian, text)
    text = re.sub(_time_re, normalize_time, text)
    text = re.sub(_time_zh_re, normalize_time_zh, text)
    text = re.sub(_time_shortform_re, normalize_time_shortform, text)
    text = re.sub(_temperature_re, normalize_temperature_zh, text)
    text = re.sub(_leftover_dot_re, normalize_leftover_dot, text)

    text = re.sub(_number_with_commas_re, normalize_number_with_commas, text)
    text = re.sub(_decimal_re, normalize_decimal, text)
    text = re.sub(_dashed_digit_re, normalize_dashed_digits, text)
    text = re.sub(_dashed_alnum_re, normalize_dashed_alnum, text)
    text = re.sub(_alnum_re, normalize_alnum, text)
    text = re.sub(_number_re, normalize_number, text)

    return text.strip()
