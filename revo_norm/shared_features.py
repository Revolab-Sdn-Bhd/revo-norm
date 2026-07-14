"""
Shared feature normalizers for TTS text normalization.

Provides temperature, measurements, fractions, x-kali, hari bulan, hijri,
and elongated word normalization for all supported languages (en, ms, zh, zh_my).
"""

import re


# Elongated word normalization
def normalize_elongated_word(word: str) -> str:
    """
    Normalize elongated words by reducing repeated characters (3+ consecutive) to 2.

    Examples:
        "betuii" -> "betui"
        "sayangnya" -> "sayangnya" (unchanged, only 2 chars)
        "celakaaa" -> "celaka"

    Args:
        word: The word to normalize

    Returns:
        Normalized word with reduced consecutive characters
    """
    # Don't normalize if it starts with 'ke-' (ordinal prefix)
    if word.lower().startswith("ke-"):
        return word

    # Reduce 3+ consecutive repeated characters to 2
    normalized = re.sub(r"(.)\1{2,}", r"\1\1", word)
    return normalized


def normalize_elongated_text(text: str) -> str:
    """
    Normalize elongated words in text.

    Args:
        text: Input text containing potential elongated words

    Returns:
        Text with elongated words normalized

    Example:
        >>> normalize_elongated_text("saya betuii sangat celakaaa")
        'saya betui sangat celaka'
    """
    words = text.split()
    normalized = []

    for word in words:
        # Skip if all uppercase (might be acronym) or contains digits
        if word.isupper() or any(c.isdigit() for c in word):
            normalized.append(word)
        # Check if it has 3+ consecutive repeated characters
        elif re.search(r"(.)\1{2,}", word.lower()):
            normalized.append(normalize_elongated_word(word))
        else:
            normalized.append(word)

    return " ".join(normalized)


# Fraction handling
# Pattern excludes dates by checking that the fraction is NOT part of a date
# Uses negative lookbehind to ensure no digit/slash before, and negative lookahead after
# Matches: "10/4", "3/4" but NOT "15/08/2025"
_FRACTION_PATTERN = re.compile(r"(?<![\d/])(\d+)\s*/\s*(\d+)(?![/\d])")


def _ms_or_id_normalizer(language: str):
    """Explicit Malay vs Indonesian normalizer choice — unknown codes fail loudly."""
    if language == "ms":
        from revo_norm.normalizer_ms import normalize_malay

        return normalize_malay
    if language == "id":
        from revo_norm.normalizer_id import normalize_indonesian

        return normalize_indonesian
    raise ValueError(f"Unsupported language for Malay/Indonesian branch: {language!r}")


def normalize_fraction(match: re.Match, language: str = "en") -> str:
    r"""
    Normalize a fraction to spoken form.

    Args:
        match: Regex match object with numerator and denominator groups
        language: Language code ('en' for English, 'ms' for Malay, 'zh' for Chinese, 'zh_my' for Malaysian-Chinese)

    Returns:
        Spoken form of the fraction

    Examples:
        >>> normalize_fraction(re.match(r'(\d+)/(\d+)', '10/4'), 'en')
        'ten over four'
        >>> normalize_fraction(re.match(r'(\d+)/(\d+)', '10/4'), 'ms')
        'sepuluh per empat'
    """
    from revo_norm.normalizer_en import text_normalize as normalize_en

    numerator = match.group(1)
    denominator = match.group(2)

    if language in ("zh", "zh_my"):
        from revo_norm.num2word_zh import to_cardinal

        numerator_spoken = to_cardinal(int(numerator))
        denominator_spoken = to_cardinal(int(denominator))
        return f"{denominator_spoken}分之{numerator_spoken}"
    elif language == "en":
        numerator_spoken = normalize_en(numerator)
        denominator_spoken = normalize_en(denominator)
        return f"{numerator_spoken} over {denominator_spoken}"
    else:
        normalize_local = _ms_or_id_normalizer(language)
        numerator_spoken = normalize_local(numerator)
        denominator_spoken = normalize_local(denominator)
        return f"{numerator_spoken} per {denominator_spoken}"


def normalize_fractions(text: str, language: str = "en") -> str:
    """
    Normalize all fractions in text to spoken form.

    Args:
        text: Input text containing fractions
        language: Language code ('en', 'ms', 'zh', 'zh_my')

    Returns:
        Text with fractions normalized

    Example:
        >>> normalize_fractions("10/4 of the students", language="en")
        'ten over four of the students'
    """
    return _FRACTION_PATTERN.sub(lambda m: normalize_fraction(m, language), text)


# Times/multiplier handling (x, X)
_X_KALI_PATTERN = re.compile(r"\b(\d+)\s*[xX]\b")


def normalize_x_kali(match: re.Match, language: str = "en") -> str:
    r"""
    Normalize "x" multiplier notation to spoken form.

    Args:
        match: Regex match object with number group
        language: Language code ('en' for English, 'ms' for Malay, 'zh' for Chinese, 'zh_my' for Malaysian-Chinese)

    Returns:
        Spoken form of the multiplier

    Examples:
        >>> normalize_x_kali(re.match(r'(\d+)[xX]', '10x'), 'en')
        'ten times'
        >>> normalize_x_kali(re.match(r'(\d+)[xX]', '10x'), 'ms')
        'sepuluh kali'
    """
    from revo_norm.normalizer_en import text_normalize as normalize_en

    number = match.group(1)

    if language in ("zh", "zh_my"):
        from revo_norm.num2word_zh import to_cardinal

        number_spoken = to_cardinal(int(number))
        if number_spoken == "二":
            return "两次"
        return f"{number_spoken}次"
    elif language == "en":
        number_spoken = normalize_en(number)
        return f"{number_spoken} times"
    else:
        normalize_local = _ms_or_id_normalizer(language)
        number_spoken = normalize_local(number)
        return f"{number_spoken} kali"


def normalize_x_kali_text(text: str, language: str = "en") -> str:
    """
    Normalize all "x" multiplier notations in text to spoken form.

    Args:
        text: Input text containing x multipliers
        language: Language code ('en', 'ms', 'zh', 'zh_my')

    Returns:
        Text with x multipliers normalized

    Example:
        >>> normalize_x_kali_text("10x faster", language="en")
        'ten times faster'
    """
    return _X_KALI_PATTERN.sub(lambda m: normalize_x_kali(m, language), text)


# Temperature handling
_TEMPERATURE_PATTERN = re.compile(r"\b(-?\d+(?:[\.,]\d+)?)\s*([CFK])\b", re.IGNORECASE)

_TEMPERATURE_UNITS = {
    # id "selsius": phonetic spelling — Indonesian G2P reads "c" as "ch"
    "c": {"en": "celsius", "ms": "celcius", "id": "selsius", "zh": "摄氏度", "zh_my": "摄氏度"},
    "f": {
        "en": "fahrenheit",
        "ms": "fahrenheit",
        "id": "fahrenheit",
        "zh": "华氏度",
        "zh_my": "华氏度",
    },
    "k": {"en": "kelvin", "ms": "kelvin", "id": "kelvin", "zh": "开尔文", "zh_my": "开尔文"},
}


def normalize_temperature(match: re.Match, language: str = "en") -> str:
    r"""
    Normalize temperature notation to spoken form.

    Args:
        match: Regex match object with value and unit groups
        language: Language code ('en' for English, 'ms' for Malay, 'zh' for Chinese, 'zh_my' for Malaysian-Chinese)

    Returns:
        Spoken form of the temperature

    Examples:
        >>> normalize_temperature(re.match(r'(-?\d+)\s*([CFK])', '25C'), 'en')
        'twenty five celsius'
        >>> normalize_temperature(re.match(r'(-?\d+)\s*([CFK])', '25C'), 'ms')
        'dua puluh lima celcius'
    """
    from revo_norm.normalizer_en import text_normalize as normalize_en

    value = match.group(1).replace(",", ".")
    unit = match.group(2).lower()

    if language in ("zh", "zh_my"):
        from revo_norm.num2word_zh import to_cardinal

        unit_spoken = _TEMPERATURE_UNITS[unit][language]
        num_val = float(value)
        num_int = int(num_val)
        cardinal = to_cardinal(num_int) if num_val == num_int else to_cardinal(num_val)
        return f"{cardinal}{unit_spoken}"
    elif language == "en":
        value_spoken = normalize_en(value)
        unit_spoken = _TEMPERATURE_UNITS[unit]["en"]
        return f"{value_spoken} {unit_spoken}"
    else:
        normalize_local = _ms_or_id_normalizer(language)
        value_spoken = normalize_local(value)
        unit_spoken = _TEMPERATURE_UNITS[unit][language]
        return f"{value_spoken} {unit_spoken}"


def normalize_temperatures(text: str, language: str = "en") -> str:
    """
    Normalize all temperature notations in text to spoken form.

    Args:
        text: Input text containing temperatures
        language: Language code ('en', 'ms', 'zh', 'zh_my')

    Returns:
        Text with temperatures normalized

    Example:
        >>> normalize_temperatures("25C outside", language="en")
        'twenty five celsius outside'
    """
    return _TEMPERATURE_PATTERN.sub(lambda m: normalize_temperature(m, language), text)


# IC (Malaysian ID) handling
_IC_PATTERN = re.compile(r"\b(\d{6})-?(\d{2})-?(\d{4})\b")


def normalize_ic(match: re.Match, language: str = "en") -> str:
    r"""
    Normalize Malaysian IC number to spoken form.

    Args:
        match: Regex match object with 3 groups (birth, place, code)
        language: Language code ('en' for English, 'ms' for Malay, 'zh' for Chinese, 'zh_my' for Malaysian-Chinese)

    Returns:
        Spoken form of the IC number

    Examples:
        >>> normalize_ic(re.match(r'(\d{6})-?(\d{2})-?(\d{4})', '911111-01-1111'), 'en')
        'nine one one one one one zero one one one one one'
        >>> normalize_ic(re.match(r'(\d{6})-?(\d{2})-?(\d{4})', '911111-01-1111'), 'ms')
        'satu satu satu satu satu satu kosong satu satu satu satu satu'
    """
    from revo_norm.normalizer_en import text_normalize as normalize_en

    part1 = match.group(1)
    part2 = match.group(2)
    part3 = match.group(3)

    if language in ("zh", "zh_my"):
        from revo_norm.num2word_zh import to_cardinal

        # Speak each digit individually
        spoken = []
        for part in [part1, part2, part3]:
            for digit in part:
                spoken.append(to_cardinal(int(digit)))
        return " ".join(spoken)
    elif language == "en":
        # Speak each digit individually
        spoken = []
        for part in [part1, part2, part3]:
            for digit in part:
                spoken.append(normalize_en(digit))
        return " ".join(spoken)
    else:
        # Speak each digit individually
        normalize_local = _ms_or_id_normalizer(language)
        spoken = []
        for part in [part1, part2, part3]:
            for digit in part:
                spoken.append(normalize_local(digit))
        return " ".join(spoken)


def normalize_ic_numbers(text: str, language: str = "en") -> str:
    """
    Normalize all Malaysian IC numbers in text to spoken form.

    Args:
        text: Input text containing IC numbers
        language: Language code ('en', 'ms', 'zh', 'zh_my')

    Returns:
        Text with IC numbers normalized

    Example:
        >>> normalize_ic_numbers("IC: 911111-01-1111", language="en")
        'IC: nine one one one one one zero one one one one one'
    """
    return _IC_PATTERN.sub(lambda m: normalize_ic(m, language), text)


# Distance/volume/weight/duration patterns
_DISTANCE_PATTERN = re.compile(
    r"\b(-?\d+(?:[\.,]\d+)?)\s*(km|m|cm|mm|ft|in|yd|mi|batu|kaki|inci)\b", re.IGNORECASE
)

_VOLUME_PATTERN = re.compile(r"\b(-?\d+(?:[\.,]\d+)?)\s*(ml|l|gal)\b", re.IGNORECASE)

_WEIGHT_PATTERN = re.compile(r"\b(-?\d+(?:[\.,]\d+)?)\s*(kg|g|mg|lb|oz)\b", re.IGNORECASE)

_DURATION_PATTERN = re.compile(
    r"\b(\d+)\s*(jam|minit|saat|hours?|minutes?|seconds?)\b", re.IGNORECASE
)

# Area pattern (e.g., "1000 sq ft", "500 sqft")
_AREA_PATTERN = re.compile(r"\b(-?\d+(?:[\.,]\d+)?)\s*(sq\s+ft|sqft)\b", re.IGNORECASE)


# Unit mappings for distance/volume/weight
_DISTANCE_UNITS_EN: dict[str, str] = {
    "km": "kilometers",
    "m": "meters",
    "cm": "centimeters",
    "mm": "millimeters",
    "ft": "feet",
    "in": "inches",
    "yd": "yards",
    "mi": "miles",
    "batu": "miles",
    "kaki": "feet",
    "inci": "inches",
}

_DISTANCE_UNITS_MS: dict[str, str] = {
    "km": "kilometer",
    "m": "meter",
    "cm": "sentimeter",
    "mm": "milimeter",
    "ft": "kaki",
    "in": "inci",
    "yd": "ela",
    "mi": "batu",
    "batu": "batu",
    "kaki": "kaki",
    "inci": "inci",
}

_VOLUME_UNITS_EN: dict[str, str] = {
    "ml": "milliliters",
    "l": "liters",
    "gal": "gallons",
}

_VOLUME_UNITS_MS: dict[str, str] = {
    "ml": "mililiter",
    "l": "liter",
    "gal": "gelen",
}

_WEIGHT_UNITS_EN: dict[str, str] = {
    "kg": "kilograms",
    "g": "grams",
    "mg": "milligrams",
    "lb": "pounds",
    "oz": "ounces",
}

_WEIGHT_UNITS_MS: dict[str, str] = {
    "kg": "kilogram",
    "g": "gram",
    "mg": "miligram",
    "lb": "paun",
    "oz": "auns",
}

# Indonesian unit words — standalone tables, not derived from the Malay ones
# ("batu" is left untranslated for id — it means "stone" in Indonesian)
_DISTANCE_UNITS_ID: dict[str, str] = {
    "km": "kilometer",
    "m": "meter",
    "cm": "sentimeter",
    "mm": "milimeter",
    "ft": "kaki",
    "in": "inci",
    "yd": "yard",
    "mi": "mil",
    "batu": "batu",
    "kaki": "kaki",
    "inci": "inci",
}

_VOLUME_UNITS_ID: dict[str, str] = {
    "ml": "mililiter",
    "l": "liter",
    "gal": "galon",
}

_WEIGHT_UNITS_ID: dict[str, str] = {
    "kg": "kilogram",
    "g": "gram",
    "mg": "miligram",
    "lb": "pon",
    "oz": "ons",
}

# Duration unit mapping
_DURATION_UNITS_EN: dict[str, str] = {
    "jam": "hours",
    "minit": "minutes",
    "saat": "seconds",
    "hour": "hour",
    "hours": "hours",
    "minute": "minute",
    "minutes": "minutes",
    "second": "second",
    "seconds": "seconds",
}

_DURATION_UNITS_MS: dict[str, str] = {
    "jam": "jam",
    "minit": "minit",
    "saat": "saat",
    "hour": "jam",
    "hours": "jam",
    "minute": "minit",
    "minutes": "minit",
    "second": "saat",
    "seconds": "saat",
}

_DURATION_UNITS_ID: dict[str, str] = {
    "jam": "jam",
    "minit": "menit",
    "saat": "detik",
    "hour": "jam",
    "hours": "jam",
    "minute": "menit",
    "minutes": "menit",
    "second": "detik",
    "seconds": "detik",
}

# Area unit mappings (e.g., "sq ft" → "square feet")
_AREA_UNITS_EN: dict[str, str] = {
    "sq ft": "square feet",
    "sqft": "square feet",
}

_AREA_UNITS_MS: dict[str, str] = {
    "sq ft": "kaki persegi",
    "sqft": "kaki persegi",
}

_AREA_UNITS_ID: dict[str, str] = {
    "sq ft": "kaki persegi",
    "sqft": "kaki persegi",
}

# Chinese Measurement unit mappings
_MEASUREMENT_ZH_UNITS = {
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


def normalize_distance(match: re.Match, language: str = "en") -> str:
    """Normalize distance notation to spoken form."""
    from revo_norm.normalizer_en import text_normalize as normalize_en

    value = match.group(1).replace(",", ".")
    unit = match.group(2).lower()

    if language == "en":
        value_spoken = normalize_en(value)
        unit_spoken = _DISTANCE_UNITS_EN.get(unit, unit)
        return f"{value_spoken} {unit_spoken}"
    else:
        normalize_local = _ms_or_id_normalizer(language)
        units = _DISTANCE_UNITS_ID if language == "id" else _DISTANCE_UNITS_MS
        value_spoken = normalize_local(value)
        unit_spoken = units.get(unit, unit)
        return f"{value_spoken} {unit_spoken}"


def normalize_volume(match: re.Match, language: str = "en") -> str:
    """Normalize volume notation to spoken form."""
    from revo_norm.normalizer_en import text_normalize as normalize_en

    value = match.group(1).replace(",", ".")
    unit = match.group(2).lower()

    if language == "en":
        value_spoken = normalize_en(value)
        unit_spoken = _VOLUME_UNITS_EN.get(unit, unit)
        return f"{value_spoken} {unit_spoken}"
    else:
        normalize_local = _ms_or_id_normalizer(language)
        units = _VOLUME_UNITS_ID if language == "id" else _VOLUME_UNITS_MS
        value_spoken = normalize_local(value)
        unit_spoken = units.get(unit, unit)
        return f"{value_spoken} {unit_spoken}"


def normalize_weight(match: re.Match, language: str = "en") -> str:
    """Normalize weight notation to spoken form."""
    from revo_norm.normalizer_en import text_normalize as normalize_en

    value = match.group(1).replace(",", ".")
    unit = match.group(2).lower()

    if language == "en":
        value_spoken = normalize_en(value)
        unit_spoken = _WEIGHT_UNITS_EN.get(unit, unit)
        return f"{value_spoken} {unit_spoken}"
    else:
        normalize_local = _ms_or_id_normalizer(language)
        units = _WEIGHT_UNITS_ID if language == "id" else _WEIGHT_UNITS_MS
        value_spoken = normalize_local(value)
        unit_spoken = units.get(unit, unit)
        return f"{value_spoken} {unit_spoken}"


def normalize_duration(match: re.Match, language: str = "en") -> str:
    """Normalize duration notation to spoken form."""
    from revo_norm.normalizer_en import text_normalize as normalize_en

    value = match.group(1)
    unit = match.group(2).lower()

    if language == "en":
        value_spoken = normalize_en(value)
        unit_spoken = _DURATION_UNITS_EN.get(unit, unit)
        return f"{value_spoken} {unit_spoken}"
    else:
        normalize_local = _ms_or_id_normalizer(language)
        units = _DURATION_UNITS_ID if language == "id" else _DURATION_UNITS_MS
        value_spoken = normalize_local(value)
        unit_spoken = units.get(unit, unit)
        return f"{value_spoken} {unit_spoken}"


def normalize_area(match: re.Match, language: str = "en") -> str:
    """Normalize area notation to spoken form (e.g., '1000 sq ft' → 'one thousand square feet')."""
    from revo_norm.normalizer_en import text_normalize as normalize_en

    value = match.group(1).replace(",", ".")
    unit = match.group(2).lower()

    if language == "en":
        value_spoken = normalize_en(value)
        unit_spoken = _AREA_UNITS_EN.get(unit, unit)
        return f"{value_spoken} {unit_spoken}"
    else:
        normalize_local = _ms_or_id_normalizer(language)
        units = _AREA_UNITS_ID if language == "id" else _AREA_UNITS_MS
        value_spoken = normalize_local(value)
        unit_spoken = units.get(unit, unit)
        return f"{value_spoken} {unit_spoken}"


def normalize_measurements(text: str, language: str = "en") -> str:
    """
    Normalize all distance, volume, weight, duration, and area notations in text.

    Args:
        text: Input text containing measurements
        language: Language code ('en', 'ms', 'zh', 'zh_my')

    Returns:
        Text with measurements normalized

    Example:
        >>> normalize_measurements("5km 2kg 1000 sq ft", language="en")
        'five kilometers two kilograms one thousand square feet'
    """
    if language in ("zh", "zh_my"):
        from revo_norm.normalizer_zh import normalize_decimal
        from revo_norm.num2word_zh import to_cardinal

        _measurement_zh_re = re.compile(
            r"(\d+(?:\.\d+)?)\s*(km|m|cm|mm|kg|g|mg|ml|l|litre|liter)(?![A-Za-z0-9])",
            re.IGNORECASE,
        )

        def _normalize_measurement_zh(m: re.Match) -> str:
            value = m.group(1)
            unit = m.group(2).lower()
            unit_word = _MEASUREMENT_ZH_UNITS.get(unit, unit)
            if "." in value:
                dec_words = normalize_decimal(re.match(r"(\d+)\.(\d+)", value))
                return f"{dec_words}{unit_word}"
            return f"{to_cardinal(int(value))}{unit_word}"

        return _measurement_zh_re.sub(_normalize_measurement_zh, text)

    text = _DISTANCE_PATTERN.sub(lambda m: normalize_distance(m, language), text)
    text = _VOLUME_PATTERN.sub(lambda m: normalize_volume(m, language), text)
    text = _WEIGHT_PATTERN.sub(lambda m: normalize_weight(m, language), text)
    text = _DURATION_PATTERN.sub(lambda m: normalize_duration(m, language), text)
    text = _AREA_PATTERN.sub(lambda m: normalize_area(m, language), text)
    return text


# Hari bulan (day-month) handling
_HARI_BULAN_PATTERN = re.compile(r"\b([1-9]|[12][0-9]|3[01])\s*[Hh][Bb]\b")


def normalize_hari_bulan(match: re.Match, language: str = "en") -> str:
    r"""
    Normalize "HB" (Hari Bulan) notation to spoken form.

    Args:
        match: Regex match object with day group
        language: Language code ('en' or 'ms')

    Returns:
        Spoken form of the hari bulan

    Examples:
        >>> normalize_hari_bulan(re.match(r'([1-9]|[12][0-9]|3[01])\s*[Hh][Bb]', '10HB'), 'ms')
        'sepuluh hari bulan'
    """
    from revo_norm.normalizer_en import text_normalize as normalize_en

    day = match.group(1)

    if language == "en":
        day_spoken = normalize_en(day)
        return f"{day_spoken} hari bulan"
    else:
        day_spoken = _ms_or_id_normalizer(language)(day)
        return f"{day_spoken} hari bulan"


def normalize_hari_bulan_text(text: str, language: str = "en") -> str:
    r"""
    Normalize all hari bulan notations in text to spoken form.

    Args:
        text: Input text containing hari bulan
        language: Language code ('en' or 'ms')

    Returns:
        Text with hari bulan normalized

    Example:
        >>> normalize_hari_bulan_text("10HB every year", language="ms")
        'sepuluh hari bulan every year'
    """
    if language in ("zh", "zh_my"):
        return text

    # Use a unique placeholder that cannot appear in normal text
    # This prevents interference from other normalizers (e.g., contraction handling)
    PLACEHOLDER = "__HARI_BULAN__"  # noqa: N806

    def replace_hb(match):
        from revo_norm.normalizer_en import text_normalize as normalize_en

        day = match.group(1)
        if language == "en":
            day_spoken = normalize_en(day)
            return f"{day_spoken}{PLACEHOLDER}"
        else:
            day_spoken = _ms_or_id_normalizer(language)(day)
            return f"{day_spoken}{PLACEHOLDER}"

    result = _HARI_BULAN_PATTERN.sub(replace_hb, text)
    # Replace placeholder with actual spoken form
    # Use word boundaries to ensure we don't match partial strings
    result = result.replace(PLACEHOLDER, " hari bulan")
    return result


# Hijri year handling
_HIJRI_YEAR_PATTERN = re.compile(r"\b(\d{3,4})\s*[Hh]\b")


def normalize_hijri_year(match: re.Match, language: str = "en") -> str:
    r"""
    Normalize Hijri year notation to spoken form.

    Args:
        match: Regex match object with year group
        language: Language code ('en' or 'ms')

    Returns:
        Spoken form of the Hijri year

    Examples:
        >>> normalize_hijri_year(re.match(r'(\d{3,4})\s*[Hh]', '1433H'), 'en')
        'one four three three Hijri'
        >>> normalize_hijri_year(re.match(r'(\d{3,4})\s*[Hh]', '1433H'), 'ms')
        'satu empat tiga tiga Hijri'
    """
    from revo_norm.normalizer_en import text_normalize as normalize_en

    year = match.group(1)

    if language == "en":
        # Speak each digit individually for Hijri years
        spoken = []
        for digit in year:
            spoken.append(normalize_en(digit))
        return " ".join(spoken) + " Hijri"
    else:
        normalize_local = _ms_or_id_normalizer(language)
        # Speak each digit individually for Hijri years
        spoken = []
        for digit in year:
            spoken.append(normalize_local(digit))
        suffix = "Hijriah" if language == "id" else "Hijri"
        return " ".join(spoken) + f" {suffix}"


def normalize_hijri_years(text: str, language: str = "en") -> str:
    """
    Normalize all Hijri year notations in text to spoken form.

    Args:
        text: Input text containing Hijri years
        language: Language code ('en' or 'ms')

    Returns:
        Text with Hijri years normalized

    Example:
        >>> normalize_hijri_years("Year 1433H", language="en")
        'Year one four three three Hijri'
    """
    if language in ("zh", "zh_my"):
        return text

    return _HIJRI_YEAR_PATTERN.sub(lambda m: normalize_hijri_year(m, language), text)
