"""Language packs: per-language data + hooks, registered centrally.

Every language's vocabulary lives in one pack — units, months, symbol words,
number-speaker hooks. Adding a language means adding one pack here and one
normalizer module; the pipeline reads packs through ``get_pack`` and never
branches on language codes for vocabulary.

Behavior that needs more than a word lookup (Chinese number joining, URL
speech) keeps its per-language module and is dispatched by the pack's
callable hooks, not by ``if language ==`` chains in shared code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

UnitTable = dict[str, str]
# "1234" -> "seribu dua ratus tiga puluh empat"
NumberSpeaker = Callable[[str], str]


@dataclass(frozen=True)
class LanguagePack:
    code: str
    speak_number: NumberSpeaker
    distance_units: UnitTable = field(default_factory=dict)
    volume_units: UnitTable = field(default_factory=dict)
    weight_units: UnitTable = field(default_factory=dict)
    duration_units: UnitTable = field(default_factory=dict)
    area_units: UnitTable = field(default_factory=dict)
    # Temperature unit symbol -> spoken form (keys: c, f, k)
    temperature_units: UnitTable = field(default_factory=dict)
    fraction_word: str = "per"
    # Spoken before a digit string when '-' means a negative quantity
    # ("suhu -5" -> "suhu negative five" / "negatif lima" / "负五").
    negative_word: str = "negatif"
    times_word: str = "kali"
    hijri_suffix: str = "Hijri"
    # Symbol -> spoken form for TTS-unfriendly characters (&, *, #, ...).
    # An empty-string value drops the symbol silently (en/ms "*").
    symbol_words: UnitTable = field(default_factory=dict)
    # Single digit "0"-"9" -> spoken word
    digit_words: UnitTable = field(default_factory=dict)
    # Month number ("1".."12", zero-padded variants) -> month name
    month_names: UnitTable = field(default_factory=dict)
    # Currency code/symbol -> (main unit, subunit). Missing keys fall through
    # to the extractor default ((symbol.lower(), "cents")).
    currency_names: dict[str, tuple[str, str]] = field(default_factory=dict)
    # int -> spoken cardinal for currency/decimal amounts (en uses inflect instead)
    num2word: Callable[[int], str] | None = None
    # Features that do not apply to this language (zh skips HB/Hijri)
    uses_hari_bulan: bool = True
    uses_hijri_years: bool = True
    # Full text normalizer for this language (contractions, numbers, grammar)
    normalize: Callable[[str], str] | None = None
    # Rewrites written number conventions (dotted thousands, comma decimals)
    # into the plain forms the shared pipeline expects. None = no preparse.
    preparse_number_formats: Callable[[str], str] | None = None
    # en-semantics "K/M/B/T" currency suffix expansion applies to this language
    use_en_currency_m_suffix: bool = True
    # "!" is dropped silently (TTS over-emphasis); id/zh/zh_my keep it
    drops_exclamation: bool = False


_PACKS: dict[str, LanguagePack] = {}


def register_language(pack: LanguagePack) -> None:
    """Register a pack. Re-registering the same code replaces it (tests rely on this)."""
    _PACKS[pack.code] = pack


def get_pack(language: str) -> LanguagePack:
    """Fetch the pack for a language code. Unknown codes raise ValueError."""
    code = language.strip().lower()
    try:
        return _PACKS[code]
    except KeyError:
        raise ValueError(
            f"Unsupported language: {language!r} (expected one of {tuple(_PACKS)})"
        ) from None


def supported_languages() -> tuple[str, ...]:
    """All registered language codes, registration order."""
    return tuple(_PACKS)


def _speak_en(digits: str) -> str:
    from revo_norm.normalizer_en import text_normalize

    return text_normalize(digits)


def _speak_ms(digits: str) -> str:
    from revo_norm.normalizer_ms import normalize_malay

    return normalize_malay(digits)


def _speak_id(digits: str) -> str:
    from revo_norm.normalizer_id import normalize_indonesian

    return normalize_indonesian(digits)


def _speak_zh(digits: str) -> str:
    from revo_norm.num2word_zh import to_cardinal

    # Hijri years/multipliers arrive as integers; shared features may pass
    # decimals ("25.5"), which to_cardinal handles in its float branch.
    if "." in digits:
        return to_cardinal(float(digits))
    return to_cardinal(int(digits))


def _normalize_en(text: str) -> str:
    from revo_norm.normalizer_en import text_normalize

    return text_normalize(text)


def _normalize_ms(text: str) -> str:
    from revo_norm.normalizer_ms import normalize_malay

    return normalize_malay(text)


def _normalize_id(text: str) -> str:
    from revo_norm.normalizer_id import normalize_indonesian

    return normalize_indonesian(text)


def _normalize_zh(text: str) -> str:
    from revo_norm.normalizer_zh import text_normalize_zh

    return text_normalize_zh(text)


def _normalize_zh_my(text: str) -> str:
    from revo_norm.normalizer_zh_my import text_normalize_zh_my

    return text_normalize_zh_my(text)


def _preparse_id(text: str) -> str:
    from revo_norm.normalizer_id import preparse_number_formats

    return preparse_number_formats(text)


def _num2word_ms(number: int) -> str:
    from revo_norm.num2word_ms import to_cardinal

    return to_cardinal(number)


def _num2word_id(number: int) -> str:
    from revo_norm.num2word_id import to_cardinal

    return to_cardinal(number)


_SYMBOLS_LATIN = {
    "&": "and", "+": "plus", "=": "equals", "@": "at", "#": "hash",
    "%": "percent", "$": "dollar", "EUR": "euro", "GBP": "pound",
    "©": "copyright", "®": "registered", "™": "trademark",
    "<": "less than", ">": "greater than", "|": "bar", "~": "tilde", "^": "caret",
}

_DIGITS_EN = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
              "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"}

_DIGITS_MS = {"0": "kosong", "1": "satu", "2": "dua", "3": "tiga", "4": "empat",
              "5": "lima", "6": "enam", "7": "tujuh", "8": "lapan", "9": "sembilan"}

_DIGITS_ID = {"0": "nol", "1": "satu", "2": "dua", "3": "tiga", "4": "empat",
              "5": "lima", "6": "enam", "7": "tujuh", "8": "delapan", "9": "sembilan"}

_DIGITS_ZH = {"0": "零", "1": "一", "2": "二", "3": "三", "4": "四",
              "5": "五", "6": "六", "7": "七", "8": "八", "9": "九"}

_MONTHS_EN = {
    "01": "January", "1": "January", "02": "February", "2": "February",
    "03": "March", "3": "March", "04": "April", "4": "April",
    "05": "May", "5": "May", "06": "June", "6": "June",
    "07": "July", "7": "July", "08": "August", "8": "August",
    "09": "September", "9": "September", "10": "October",
    "11": "November", "12": "December",
}

_MONTHS_MS = {
    "01": "Januari", "1": "Januari", "02": "Februari", "2": "Februari",
    "03": "Mac", "3": "Mac", "04": "April", "4": "April",
    "05": "Mei", "5": "Mei", "06": "Jun", "6": "Jun",
    "07": "Julai", "7": "Julai", "08": "Ogos", "8": "Ogos",
    "09": "September", "9": "September", "10": "Oktober",
    "11": "November", "12": "Disember",
}

_MONTHS_ID = {
    "01": "Januari", "1": "Januari", "02": "Februari", "2": "Februari",
    "03": "Maret", "3": "Maret", "04": "April", "4": "April",
    "05": "Mei", "5": "Mei", "06": "Juni", "6": "Juni",
    "07": "Juli", "7": "Juli", "08": "Agustus", "8": "Agustus",
    "09": "September", "9": "September", "10": "Oktober",
    "11": "November", "12": "Desember",
}


def _register_builtin_packs() -> None:
    register_language(
        LanguagePack(
            code="en",
            normalize=_normalize_en,
            drops_exclamation=True,
            speak_number=_speak_en,
            distance_units={
                "km": "kilometers", "m": "meters", "cm": "centimeters",
                "mm": "millimeters", "ft": "feet", "in": "inches",
                "yd": "yards", "mi": "miles", "batu": "miles",
                "kaki": "feet", "inci": "inches",
            },
            volume_units={"ml": "milliliters", "l": "liters", "gal": "gallons"},
            weight_units={
                "kg": "kilograms", "g": "grams", "mg": "milligrams",
                "lb": "pounds", "oz": "ounces",
            },
            duration_units={
                "jam": "hours", "minit": "minutes", "saat": "seconds",
                "hour": "hour", "hours": "hours", "minute": "minute",
                "minutes": "minutes", "second": "second", "seconds": "seconds",
            },
            area_units={"sq ft": "square feet", "sqft": "square feet"},
            temperature_units={"c": "celsius", "f": "fahrenheit", "k": "kelvin"},
            fraction_word="over",
            negative_word="negative",
            times_word="times",
            hijri_suffix="Hijri",
            symbol_words={
        '&': 'and',
        '+': 'plus',
        '=': 'equals',
        '@': 'at',
        '#': 'hash',
        '*': '',
        '%': 'percent',
        '$': 'dollar',
        'EUR': 'euro',
        'GBP': 'pound',
        '©': 'copyright',
        '®': 'registered',
        '™': 'trademark',
        '<': 'less than',
        '>': 'greater than',
        '|': 'bar',
        '~': 'tilde',
        '^': 'caret',
    },
            digit_words=dict(_DIGITS_EN),
            month_names=dict(_MONTHS_EN),
        )
    )
    register_language(
        LanguagePack(
            code="ms",
            normalize=_normalize_ms,
            num2word=_num2word_ms,
            drops_exclamation=True,
            speak_number=_speak_ms,
            distance_units={
                "km": "kilometer", "m": "meter", "cm": "sentimeter",
                "mm": "milimeter", "ft": "kaki", "in": "inci",
                "yd": "ela", "mi": "batu", "batu": "batu",
                "kaki": "kaki", "inci": "inci",
            },
            volume_units={"ml": "mililiter", "l": "liter", "gal": "gelen"},
            weight_units={
                "kg": "kilogram", "g": "gram", "mg": "miligram",
                "lb": "paun", "oz": "auns",
            },
            duration_units={
                "jam": "jam", "minit": "minit", "saat": "saat",
                "hour": "jam", "hours": "jam", "minute": "minit",
                "minutes": "minit", "second": "saat", "seconds": "saat",
            },
            area_units={"sq ft": "kaki persegi", "sqft": "kaki persegi"},
            temperature_units={"c": "celcius", "f": "fahrenheit", "k": "kelvin"},
            fraction_word="per",
            times_word="kali",
            hijri_suffix="Hijri",
            symbol_words={
        '&': 'and',
        '+': 'plus',
        '=': 'equals',
        '@': 'at',
        '#': 'hash',
        '*': '',
        '%': 'peratus',
        '$': 'dollar',
        'EUR': 'euro',
        'GBP': 'pound',
        '©': 'copyright',
        '®': 'registered',
        '™': 'trademark',
        '<': 'less than',
        '>': 'greater than',
        '|': 'bar',
        '~': 'tilde',
        '^': 'caret',
    },
            digit_words=dict(_DIGITS_MS),
            month_names=dict(_MONTHS_MS),
        )
    )
    register_language(
        LanguagePack(
            code="id",
            normalize=_normalize_id,
            num2word=_num2word_id,
            preparse_number_formats=_preparse_id,
            # In id money slang M = miliar (1e9), not million — the en-semantics
            # M-suffix expansion must not run; preparse rewrites Rp5M itself.
            use_en_currency_m_suffix=False,
            currency_names={"USD": ("dolar", "sen"), "$": ("dolar", "sen")},
            speak_number=_speak_id,
            # Standalone tables, not derived from the Malay ones
            # ("batu" stays "batu" — it means "stone" in Indonesian)
            distance_units={
                "km": "kilometer", "m": "meter", "cm": "sentimeter",
                "mm": "milimeter", "ft": "kaki", "in": "inci",
                "yd": "yard", "mi": "mil", "batu": "batu",
                "kaki": "kaki", "inci": "inci",
            },
            volume_units={"ml": "mililiter", "l": "liter", "gal": "galon"},
            weight_units={
                "kg": "kilogram", "g": "gram", "mg": "miligram",
                "lb": "pon", "oz": "ons",
            },
            duration_units={
                "jam": "jam", "minit": "menit", "saat": "detik",
                "hour": "jam", "hours": "jam", "minute": "menit",
                "minutes": "menit", "second": "detik", "seconds": "detik",
            },
            area_units={"sq ft": "kaki persegi", "sqft": "kaki persegi"},
            # id "selsius": phonetic spelling — Indonesian G2P reads "c" as "ch"
            temperature_units={"c": "selsius", "f": "fahrenheit", "k": "kelvin"},
            fraction_word="per",
            times_word="kali",
            hijri_suffix="Hijriah",
            negative_word="negatif",
            symbol_words={
        '&': 'and',
        '+': 'plus',
        '=': 'equals',
        '@': 'at',
        '#': 'hash',
        '*': 'star',
        '%': 'persen',
        '$': 'dollar',
        'EUR': 'euro',
        'GBP': 'pound',
        '©': 'copyright',
        '®': 'registered',
        '™': 'trademark',
        '<': 'less than',
        '>': 'greater than',
        '|': 'bar',
        '~': 'tilde',
        '^': 'caret',
    },
            digit_words=dict(_DIGITS_ID),
            month_names=dict(_MONTHS_ID),
        )
    )
    _zh_units = {
        "km": "公里", "m": "米", "cm": "厘米", "mm": "毫米", "kg": "公斤",
        "g": "克", "mg": "毫克", "ml": "毫升", "l": "升", "litre": "升",
        "liter": "升",
    }
    register_language(
        LanguagePack(
            code="zh",
            normalize=_normalize_zh,
            speak_number=_speak_zh,
            distance_units={k: v for k, v in _zh_units.items() if k in ("km", "m", "cm", "mm")},
            volume_units={k: v for k, v in _zh_units.items() if k in ("ml", "l", "litre", "liter")},
            weight_units={k: v for k, v in _zh_units.items() if k in ("kg", "g", "mg")},
            duration_units={},
            area_units={},
            temperature_units={"c": "摄氏度", "f": "华氏度", "k": "开尔文"},
            fraction_word="分之",
            times_word="次",
            negative_word="负",
            hijri_suffix="Hijri",
            symbol_words={
        '&': '和',
        '+': '加',
        '=': '等于',
        '@': '艾特',
        '#': '井',
        '*': '星号',
        '%': '巴仙',
        '$': '美元',
        'EUR': '欧元',
        'GBP': '英镑',
        '©': '版权',
        '®': '注册',
        '™': '商标',
        '<': '小于',
        '>': '大于',
        '|': '竖线',
        '~': '波浪号',
        '^': '插入符',
    },
            digit_words=dict(_DIGITS_ZH),
            uses_hari_bulan=False,
            uses_hijri_years=False,
        )
    )
    # zh_my inherits the zh vocabulary; only normalization behavior diverges
    register_language(
        LanguagePack(
            code="zh_my",
            normalize=_normalize_zh_my,
            speak_number=_speak_zh,
            distance_units={k: v for k, v in _zh_units.items() if k in ("km", "m", "cm", "mm")},
            volume_units={k: v for k, v in _zh_units.items() if k in ("ml", "l", "litre", "liter")},
            weight_units={k: v for k, v in _zh_units.items() if k in ("kg", "g", "mg")},
            duration_units={},
            area_units={},
            temperature_units={"c": "摄氏度", "f": "华氏度", "k": "开尔文"},
            fraction_word="分之",
            times_word="次",
            negative_word="负",
            hijri_suffix="Hijri",
            symbol_words={
        '&': '和',
        '+': '加',
        '=': '等于',
        '@': 'at',
        '#': 'hash',
        '*': '星号',
        '%': '巴仙',
        '$': '块',
        'EUR': '欧元',
        'GBP': '英镑',
        '©': '版权',
        '®': '注册',
        '™': '商标',
        '<': '小于',
        '>': '大于',
        '|': '竖线',
        '~': '波浪号',
        '^': '插入符',
    },
            digit_words=dict(_DIGITS_ZH),
            uses_hari_bulan=False,
            uses_hijri_years=False,
        )
    )


_register_builtin_packs()
