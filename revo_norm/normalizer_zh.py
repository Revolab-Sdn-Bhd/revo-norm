"""
Standard Chinese text normalization for TTS.

Handles numbers, percentages, and decimals in standard Chinese (普通话) spoken
form. Dates, times, currency, temperature, and measurements are handled by
entity extraction and shared_features (which respect config flags).
"""

import re

from revo_norm.num2word_zh import to_cardinal, to_year


# Numbers
_NUMBERS = {
    "0": "零",
    "1": "一",
    "2": "二",
    "3": "三",
    "4": "四",
    "5": "无",
    "6": "六",
    "7": "七",
    "8": "八",
    "9": "九",
}

# Month names (used by entity_extractor for Chinese dates)
_MONTHS = {
    "01": "一", "1": "一",
    "02": "二", "2": "二",
    "03": "三", "3": "三",
    "04": "四", "4": "四",
    "05": "五", "5": "五",
    "06": "六", "6": "六",
    "07": "七", "7": "七",
    "08": "八", "8": "八",
    "09": "九", "9": "九",
    "10": "十",
    "11": "十一",
    "12": "十二",
}

# Times
_TIMES = {
    "am": "上午",
    "pm": "晚上"
}

# Measurement unit → Chinese (used by shared_features for Chinese measurements)
_MEASUREMENT_UNITS = {
    "km": "公里",
    "m": "米",
    "cm": "厘米",
    "mm": "毫米",
    "kg": "公斤",
    "g": "克",
    "mg": "毫克",
    "ml": "毫升",
    "l": "升",
    "litre": "升",
    "liter": "升",
}

# Regex
_percentage_re = re.compile(r"(\d+(?:\.\d+)?)%")
_decimal_re = re.compile(r"(\d+)\.(\d+)")
_number_re = re.compile(r"\d+")
_number_with_commas_re = re.compile(r"\d{1,3}(?:,\d{3})+")
_measurement_re = re.compile(
    r"(\d+(?:\.\d+)?)\s*(km|m|cm|mm|kg|g|mg|ml|l|litre|liter)(?![A-Za-z0-9])",
    re.IGNORECASE,
)
_date_DMY_re = re.compile(r"(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})")
_date_YMD_re = re.compile(r"(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})")
_currency_re = re.compile(
    r"(?<!\w)(\$|£|€|RM|MYR|USD|EUR|GBP)(?:\s?)([\d,]+(?:[\.,]\d{1,2})?)(?:\s?(千|万|百万|千万|亿|百亿|千亿|万亿|兆))?",
    re.IGNORECASE,
)
_dashed_digit_re = re.compile(r"(?<![A-Za-z])([+\d]+(?:-[\d]+)+)(?![A-Za-z])")
_dashed_alnum_re = re.compile(
    r"([A-Za-z0-9]+(?:-[A-Za-z0-9]+)+)"
)
_alnum_re = re.compile(r"((?=[A-Za-z0-9]*[A-Za-z])(?=[A-Za-z0-9]*\d)[A-Za-z0-9]+)")
_time_re = re.compile(
    r"(\d{1,2})[:\.](\d{2})\s*(?:(am|pm|a\.m\.|p\.m\.))",
    re.IGNORECASE,
)
_time_re_zh = re.compile(
    r"(?:(凌晨|早上|中午|下午|傍晚|晚上))\s*(\d{1,2})[:\.](\d{2})",
    re.IGNORECASE,
)
_time_no_meridian_re = re.compile(
    r"(?<!凌晨)(?<!早上)(?<!中午)(?<!下午)(?<!傍晚)(?<!晚上)"
    r"\b(\d{1,2})[:\.](\d{2})(?!\s*(?:am|pm|a\.m\.|p\.m\.))"
    r"(?!.*%)",
    re.IGNORECASE,
)


def normalize_percentage(m: re.Match) -> str:
    number = m.group(1)
    if "." in number:
        whole, frac = number.split(".")
        frac_words = "".join(to_cardinal(int(d)) for d in frac)
        return f"百分之{to_cardinal(int(whole))}点{frac_words}"
    return f"百分之{to_cardinal(int(float(number)))}"


def normalize_decimal(m: re.Match) -> str:
    whole, frac = m.group(1), m.group(2)
    frac_words = "".join(to_cardinal(int(d)) for d in frac)
    return f"{to_cardinal(int(whole))}点{frac_words}"


def normalize_number(m: re.Match) -> str:
    num_str = m.group(0)
    num = int(num_str)
    if len(num_str) == 4 and 1000 <= num <= 2099:
        return to_year(num)
    return to_cardinal(num)


def normalize_number_with_commas(m: re.Match) -> str:
    num_str = m.group(0).replace(",", "")
    return to_cardinal(int(num_str))


def normalize_measurement(m: re.Match) -> str:
    value = m.group(1)
    unit = m.group(2).lower()
    unit_word = _MEASUREMENT_UNITS.get(unit, unit)
    if "." in value:
        dec_words = normalize_decimal(re.match(r"(\d+)\.(\d+)", value))
        return f"{dec_words}{unit_word}"
    return f"{to_cardinal(int(float(value)))}{unit_word}"


def normalize_date_DMY(m: re.Match) -> str:
    day, month, year = m.groups()
    month_str = _MONTHS.get(month, month)
    return f"{to_year(int(year))}年{month_str}月{to_cardinal(int(day))}日"


def normalize_date_YMD(m: re.Match) -> str:
    year, month, day = m.groups()
    month_str = _MONTHS.get(month, month)
    return f"{to_year(int(year))}年{month_str}月{to_cardinal(int(day))}日"


def normalize_currency(m: re.Match) -> str:
    symbol = m.group(1).upper()
    amount = m.group(2).replace(",", "")
    magnitude = m.group(3) or ""

    if symbol.upper() in ("RM", "MYR"):
        unit_main, unit_sub = "令吉", "仙"
    elif symbol in ("$", "USD"):
        unit_main, unit_sub = "美元", "分"
    elif symbol in ("£", "GBP"):
        unit_main, unit_sub = "英磅", "便士"
    elif symbol in ("€", "EUR"):
        unit_main, unit_sub = "欧元", "分"
    else:
        unit_main, unit_sub = "元", "分"

    if "." in amount:
        whole, frac = amount.split(".")
        frac = frac.ljust(2, "0")[:2]
        if frac != "00":
            return f"{to_cardinal(int(whole))}{magnitude}{unit_main}{to_cardinal(int(frac))}{unit_sub}"
        else:
            return f"{to_cardinal(int(whole))}{magnitude}{unit_main}"
        
    return f"{to_cardinal(int(amount))}{magnitude}{unit_main}"


def normalize_dashed_digits(m: re.Match) -> str:
    raw_str = m.group(1)
    print(raw_str)
    return " ".join(_NUMBERS.get(ch, ch) for ch in raw_str if ch in _NUMBERS)


def normalize_dashed_alnum(m: re.Match) -> str:
    raw_str = m.group(1)
    return " ".join(_NUMBERS.get(ch, ch) for ch in raw_str if ch != '-')


def normalize_alnum(m: re.Match) -> str:
    raw_str = m.group(1)
    return " ".join(_NUMBERS.get(ch, ch) for ch in raw_str)


def normalize_time(m):
    hour, minute, meridian = m.groups()
    hour_word = to_cardinal(int(hour))
    minute_word = to_cardinal(int(minute))

    meridian_word = ""
    if meridian:
        meridian_word = meridian if len(meridian) > 2 else f"{meridian[0]}m"

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
        return "凌晨十二点"
    # Special case for noon (12:00)
    if hour_int == 12 and minute_int == 0:
        return "中午十二点"

    hour_word = to_cardinal(hour_int)
    minute_word = to_cardinal(minute_int)

    if minute_word == "零":
        return f"{hour_word}点"
    else:
        return f"{hour_word}点{minute_word}分"


def text_normalize_zh(text: str) -> str:
    """Main Chinese text normalization function."""
    text = re.sub(_percentage_re, normalize_percentage, text)
    text = re.sub(_date_DMY_re, normalize_date_DMY, text)
    text = re.sub(_date_YMD_re, normalize_date_YMD, text)
    text = re.sub(_measurement_re, normalize_measurement, text)
    text = re.sub(_currency_re, normalize_currency, text)
    text = re.sub(_time_no_meridian_re, normalize_time_no_meridian, text)
    text = re.sub(_time_re, normalize_time, text)
    text = re.sub(_time_re_zh, normalize_time_zh, text)

    text = re.sub(_number_with_commas_re, normalize_number_with_commas, text)
    text = re.sub(_decimal_re, normalize_decimal, text)
    text = re.sub(_dashed_digit_re, normalize_dashed_digits, text)
    text = re.sub(_dashed_alnum_re, normalize_dashed_alnum, text)
    text = re.sub(_alnum_re, normalize_alnum, text)
    text = re.sub(_number_re, normalize_number, text)

    return text.strip()
