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
    _percentage_re,
    _decimal_re, normalize_decimal,
    _number_re, normalize_number,
    _number_with_commas_re, normalize_number_with_commas,
    _measurement_re, normalize_measurement,
    _date_DMY_re,
    _date_YMD_re,
    _currency_re,
    _dashed_digit_re, normalize_dashed_digits,
    _dashed_alnum_re, normalize_dashed_alnum,
    _alnum_re, normalize_alnum
)
from revo_norm.num2word_zh import to_cardinal, to_year

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


def normalize_date_DMY(m: re.Match) -> str:
    day, month, year = m.groups()
    month_str = _MONTHS.get(month, month)
    return f"{to_year(int(year))}年{month_str}月{to_cardinal(int(day))}号"


def normalize_date_YMD(m: re.Match) -> str:
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


def text_normalize_zh_my(text: str) -> str:
    """Main Malaysian Chinese text normalization function."""
    text = re.sub(_percentage_re, normalize_percentage, text)
    text = re.sub(_date_DMY_re, normalize_date_DMY, text)
    text = re.sub(_date_YMD_re, normalize_date_YMD, text)
    text = re.sub(_measurement_re, normalize_measurement, text)
    text = re.sub(_currency_re, normalize_currency, text)

    text = re.sub(_number_with_commas_re, normalize_number_with_commas, text)
    text = re.sub(_decimal_re, normalize_decimal, text)
    text = re.sub(_dashed_digit_re, normalize_dashed_digits, text)
    text = re.sub(_dashed_alnum_re, normalize_dashed_alnum, text)
    text = re.sub(_alnum_re, normalize_alnum, text)
    text = re.sub(_number_re, normalize_number, text)

    return text.strip()
