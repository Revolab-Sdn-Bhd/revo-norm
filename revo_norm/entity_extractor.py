"""
Entity extraction and protection system for text normalization.

This module provides a framework for extracting entities from text before
other normalization steps, preventing pattern conflicts and allowing for
context-aware entity processing.

Architecture:
1. Extract entities → replace with placeholders
2. Process non-entity text safely
3. Restore entities as spoken form
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import inflect


class EntityType(str, Enum):
    """Types of entities that can be extracted."""

    URL = "url"
    EMAIL = "email"
    DATE = "date"
    TIME = "time"
    CURRENCY = "currency"
    FRACTION = "fraction"
    TEMPERATURE = "temperature"
    IC = "ic"
    HARI_BULAN = "hari_bulan"
    HIJRI = "hijri"
    X_KALI = "x_kali"
    ADDRESS_SLASH = "address_slash"
    PHONE = "phone"
    VERSION = "version"


@dataclass
class Entity:
    """
    Represents an extracted entity from text.

    Attributes:
        type: Entity type (URL, email, date, etc.)
        text: Original matched text
        start: Start position in original text
        end: End position in original text
        metadata: Additional information (language, format, etc.)
        placeholder_id: ID for placeholder generation
    """

    type: EntityType
    text: str
    start: int
    end: int
    metadata: dict = field(default_factory=dict)
    placeholder_id: int = 0


class EntityExtractor:
    """
    Extracts entities from text and protects them with placeholders.

    This allows safe processing of the rest of the text without interfering
    with entity patterns.
    """

    def __init__(self):
        self.entities: list[Entity] = []
        self.next_id = 1

        # Entity patterns (sorted by specificity - most specific first)
        self.patterns = {
            # URLs and emails (must be first to prevent IP/decimal issues)
            EntityType.URL: self._compile_url_patterns(),
            EntityType.EMAIL: self._compile_email_patterns(),
            # Phone numbers (must be before numbers get normalized)
            EntityType.PHONE: self._compile_phone_patterns(),
            # Version numbers (must be before dates/ordinals)
            EntityType.VERSION: self._compile_version_patterns(),
            # Currency (must be early to protect from acronym/abbreviation expansion)
            EntityType.CURRENCY: self._compile_currency_patterns(),
            # Date and time patterns
            EntityType.DATE: self._compile_date_patterns(),
            EntityType.TIME: self._compile_time_patterns(),
            # Existing Malaya features
            EntityType.TEMPERATURE: self._compile_temperature_patterns(),
            EntityType.ADDRESS_SLASH: self._compile_address_slash_patterns(),
            EntityType.FRACTION: self._compile_fraction_patterns(),
            EntityType.X_KALI: self._compile_x_kali_patterns(),
            EntityType.IC: self._compile_ic_patterns(),
            EntityType.HARI_BULAN: self._compile_hari_bulan_patterns(),
            EntityType.HIJRI: self._compile_hijri_patterns(),
        }

    def _compile_url_patterns(self) -> re.Pattern:
        """Compile URL detection patterns."""
        return re.compile(
            r"(?:https?://|ftp://|www\.)[^\s]+|"  # Protocol-based URLs
            r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/[^\s]*)?|"  # IP addresses
            r"\b[A-Za-z0-9-]+\.[A-Za-z]{2,}(?:/[^\s]*)?",  # Simple domains
            re.IGNORECASE,
        )

    def _compile_email_patterns(self) -> re.Pattern:
        """Compile email detection patterns."""
        return re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            re.IGNORECASE,
        )

    def _compile_version_patterns(self) -> re.Pattern:
        """Compile version number patterns (e.g., 3.14.159, 1.0.0)."""
        return re.compile(r"\b(?!\d{4}\.\d{1,2}\.\d{1,2}\b)(\d+)(?:\.\d+){2,}\b")

    def _compile_phone_patterns(self) -> re.Pattern:
        """Compile phone number patterns (Malaysian formats)."""
        return re.compile(
            r"(?<!\w)"
            r"(?:"
            r"\+?6?01\d[-\s]?\d{3,4}[-\s]?\d{4}"  # mobile: 012-345 6789
            r"|\+?6?0\d[-\s]?\d{4}[-\s]?\d{4}"     # landline: 03-8888 9999
            r"|1[-\s]?[348]00[-\s]?\d{2}[-\s]?\d{4}" # toll-free: 1-300-88-6688
            r"|154\d{2}"                              # hotline: 15454
            r")"
            r"(?!\w)",
        )

    def _compile_currency_patterns(self) -> re.Pattern:
        """
        Compile currency detection patterns.

        Matches:
        - RM + amount: RM100, RM 50.50, RM1,000
        - USD + amount: USD100, USD 50.50
        - $ + amount: $100, $ 50.50
        - € + amount: €100, € 50.50
        - £ + amount: £100, £ 50.50
        - Also handles suffixes: RM30K, RM1M, RM2B, RM1T (thousands, millions, billions, trillions)
        """
        # Pattern: currency symbol (RM, USD, EUR, GBP, MYR, $, £, €) + optional space + amount
        # Amount can have commas and decimals: 1,000.50
        # Optional suffix: K (thousands), M (millions), B (billions), T (trillions)
        return re.compile(
            r"(?<!\w)(RM|USD|EUR|GBP|MYR|\$|£|€)(?:\s?)([\d,]+(?:[\.,]\d{1,2})?)(?:[KMBT])?\b",
            re.IGNORECASE,
        )

    def _compile_date_patterns(self) -> re.Pattern:
        """
        Compile date detection patterns.

        Matches:
        - DD/MM/YYYY, MM/DD/YYYY: 15/08/2025
        - YYYY-MM-DD: 2025-08-15
        - DD Month YYYY: 15 August 2025
        - Month DD, YYYY: August 15, 2025
        """
        patterns = [
            # Slash format: DD/MM/YYYY or MM/DD/YYYY
            r"(?<![A-Za-z0-9_])\d{1,2}/\d{1,2}/\d{4}(?![A-Za-z0-9_])",
            # Dash format: YYYY-MM-DD or YYYY-M-D
            r"(?<![A-Za-z0-9_])\d{4}-\d{1,2}-\d{1,2}(?![A-Za-z0-9_])",
            # Month name format: 15 August 2025
            r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|"
            r"September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|"
            r"Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b",
            # Month name format: August 15, 2025
            r"\b(?:January|February|March|April|May|June|July|August|September|"
            r"October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|"
            r"Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b",
        ]
        return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)

    def _compile_time_patterns(self) -> re.Pattern:
        """
        Compile time detection patterns.

        Matches:
        - HH:MM: 3:30, 14:45
        - HH:MM AM/PM: 3:30 pm, 11:59 AM
        - HH:MM Malay meridian: 7:30 pagi, 2:45 petang, 12:00 malam
        - HH:MM:SS: 14:30:45
        """
        patterns = [
            # HH:MM with Malay meridian (pagi/petang/malam/tengah hari) — must be before generic
            r"\b\d{1,2}:\d{2}\s*(?:pagi|petang|malam|tengah\s+hari)\b",
            # HH:MM AM/PM format
            r"\b\d{1,2}:\d{2}\s*(?:am|pm|a\.m\.|p\.m\.)?(?![A-Za-z0-9_])",
            # HH:MM:SS format
            r"\b\d{1,2}:\d{2}:\d{2}\b",
        ]
        return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)

    def _compile_temperature_patterns(self) -> re.Pattern:
        """Compile temperature detection patterns."""
        # This matches: 25C, 25°C, 25F, -5C, etc.
        return re.compile(r"\b(-?\d+(?:[\.,]\d+)?)\s*(?:°)?([CFK])\b", re.IGNORECASE)

    def _compile_fraction_patterns(self) -> re.Pattern:
        """
        Compile fraction detection patterns.

        Updated to exclude dates by using negative lookbehind/lookahead.
        Matches: 10/4, 3/4 but NOT 15/08/2025
        """
        return re.compile(r"(?<![\d/])(\d+)\s*/\s*(\d+)(?![/\d])")

    def _compile_address_slash_patterns(self) -> re.Pattern:
        """Compile address slash patterns (e.g., Jalan Setia 3/4, Jalan SS2/72, 5/6A)."""
        return re.compile(
            r"\b(?:Jalan|Lorong|Taman|Bukit|Kampung|Tingkat|Lintang|"
            r"Pesisir|Persiaran|Lebuh|Medan|Lengkung|Halaman)\s+"
            r"(?:\S+\s+)?"
            r"(\d+)\s*/\s*(\d+)\b"
            r"|"
            r"\b(?:Jalan|Lorong|Taman|Bukit|Kampung|Tingkat|Lintang|"
            r"Pesisir|Persiaran|Lebuh|Medan|Lengkung|Halaman)\s+"
            r"([A-Za-z]*\d+)\s*/\s*(\d+)\b",
            re.IGNORECASE,
        )

    def _compile_x_kali_patterns(self) -> re.Pattern:
        """Compile x-kali multiplier patterns."""
        return re.compile(r"\b(\d+)\s*[xX]\b")

    def _compile_ic_patterns(self) -> re.Pattern:
        """Compile Malaysian IC number patterns."""
        return re.compile(r"\b(\d{6})-?(\d{2})-?(\d{4})\b")

    def _compile_hari_bulan_patterns(self) -> re.Pattern:
        """Compile hari bulan patterns."""
        return re.compile(r"\b([1-9]|[12]\d|3[01])\s*[Hh][Bb]\b")

    def _compile_hijri_patterns(self) -> re.Pattern:
        """Compile Hijri year patterns."""
        return re.compile(r"\b(\d{3,4})\s*[Hh]\b")

    def extract(
        self,
        text: str,
        enabled_entities: Optional[list[EntityType]] = None,
    ) -> tuple[str, list[Entity]]:
        """
        Extract all entities from text and replace with placeholders.

        Args:
            text: Input text to extract entities from
            enabled_entities: List of entity types to extract (None = all)

        Returns:
            Tuple of (protected_text, entities_list)

        Example:
            >>> extractor = EntityExtractor()
            >>> protected, entities = extractor.extract("On 15/08/2025")
            >>> print(protected)
            "On __DATE_1__"
            >>> print(entities[0].text)
            "15/08/2025"
        """
        self.entities = []
        self.next_id = 1
        protected_text = text

        # Determine which entity types to extract
        if enabled_entities is None:
            enabled_entities = list(self.patterns.keys())

        # Extract each entity type
        for entity_type in enabled_entities:
            if entity_type in self.patterns:
                protected_text = self._extract_by_type(protected_text, entity_type)

        # Sort entities by position (for proper restoration)
        self.entities.sort(key=lambda e: e.start)

        return protected_text, self.entities

    def _extract_by_type(self, text: str, entity_type: EntityType) -> str:
        """Extract all entities of a specific type and replace with placeholders."""

        def replace_with_placeholder(match: re.Match) -> str:
            entity = Entity(
                type=entity_type,
                text=match.group(0),
                start=match.start(),
                end=match.end(),
                placeholder_id=self.next_id,
            )
            self.entities.append(entity)
            # Use triple-angle-brackets to avoid basic normalization
            # Format: <<<URL_1>>>, <<<DATE_2>>>, etc.
            # This format is unlikely to appear in normal text and won't be processed
            placeholder = f"<<<{entity_type.value.upper()}_{self.next_id}>>>"
            self.next_id += 1
            return placeholder

        return self.patterns[entity_type].sub(  # type: ignore[no-any-return]
            replace_with_placeholder, text
        )

    def restore(self, text: str, language: str) -> str:
        """
        Convert entity placeholders back to spoken form.

        Args:
            text: Text with entity placeholders
            language: Target language ('en' or 'ms')

        Returns:
            Text with entities converted to spoken form

        Example:
            >>> extractor = EntityExtractor()
            >>> protected, entities = extractor.extract("15/08/2025")
            >>> processed = process_text(protected)
            >>> result = extractor.restore(processed, "en")
            >>> print(result)
            "fifteenth of August two thousand and twenty-five"
        """
        result = text

        # Sort entities in reverse order (by position) to handle overlaps correctly
        for entity in reversed(self.entities):
            placeholder = f"<<<{entity.type.value.upper()}_{entity.placeholder_id}>>>"
            if placeholder in result:
                spoken = self._convert_entity_to_spoken(entity, language)
                result = result.replace(placeholder, spoken, 1)

        return result

    def _convert_entity_to_spoken(self, entity: Entity, language: str) -> str:
        """Convert an entity to its spoken form based on type and language."""
        # Import here to avoid circular dependencies
        from revo_norm.shared_features import (
            normalize_fractions,
            normalize_hari_bulan_text,
            normalize_hijri_years,
            normalize_ic_numbers,
            normalize_temperatures,
            normalize_x_kali_text,
        )
        from revo_norm.text_normalizer import email_to_spoken, url_to_spoken

        if entity.type == EntityType.URL:
            return url_to_spoken(entity.text, language)

        if entity.type == EntityType.EMAIL:
            return email_to_spoken(entity.text, language)

        if entity.type == EntityType.CURRENCY:
            return self._convert_currency_to_spoken(entity.text, language)

        if entity.type == EntityType.DATE:
            return self._convert_date_to_spoken(entity.text, language)

        if entity.type == EntityType.TIME:
            return self._convert_time_to_spoken(entity.text, language)

        if entity.type == EntityType.TEMPERATURE:
            # Call the normalize_temperatures function with the entity text
            return normalize_temperatures(entity.text, language)

        if entity.type == EntityType.PHONE:
            return self._convert_phone_to_spoken(entity.text, language)

        if entity.type == EntityType.VERSION:
            return self._convert_version_to_spoken(entity.text, language)

        if entity.type == EntityType.FRACTION:
            # Call the normalize_fractions function with the entity text
            return normalize_fractions(entity.text, language)

        if entity.type == EntityType.ADDRESS_SLASH:
            return self._convert_address_slash_to_spoken(entity.text, language)

        if entity.type == EntityType.X_KALI:
            # Call the normalize_x_kali_text function with the entity text
            return normalize_x_kali_text(entity.text, language)

        if entity.type == EntityType.IC:
            # Call the normalize_ic_numbers function with the entity text
            return normalize_ic_numbers(entity.text, language)

        if entity.type == EntityType.HARI_BULAN:
            # Call the normalize_hari_bulan_text function with the entity text
            return normalize_hari_bulan_text(entity.text, language)

        if entity.type == EntityType.HIJRI:
            # Call the normalize_hijri_years function with the entity text
            return normalize_hijri_years(entity.text, language)

        # Fallback: return original text
        return entity.text

    @staticmethod
    def _is_chinese(language: str) -> bool:
        return language in ("zh", "zh_my")

    def _date_to_chinese(self, m: re.Match, type: str) -> str:
        from revo_norm.normalizer_zh import normalize_date_dmy, normalize_date_ymd
        if type == "DMY":
            return normalize_date_dmy(m)
        elif type == "YMD":
            return normalize_date_ymd(m)

    def _time_to_chinese(self, language: str, hour: str, minute: str, second: str | None, ampm: str | None) -> str:
        from revo_norm.num2word_zh import to_cardinal
        h, m = int(hour), int(minute)
        meridian = ""
        if ampm:
            clean = ampm.replace(".", "").lower()
            if clean in ("pm", "p.m.") or ampm in ["下午", "傍晚", "晚上"]:
                meridian = "下午" if h <= 6 else "晚上"
            elif clean in ("am", "a.m.") or ampm in ["上午", "早上"]:
                meridian = "上午" if language == "zh" else "早上"
        time_str = f"{to_cardinal(h)}点" if m == 0 else f"{to_cardinal(h)}点{to_cardinal(m)}分"
        if second:
            time_str += f"{to_cardinal(int(second))}秒"
        return f"{meridian}{time_str}"

    def _get_ordinal_suffix(self, day: int) -> str:
        """Get ordinal suffix for a number (1st, 2nd, 3rd, 4th, etc.)."""
        if 11 <= day <= 13:
            return "th"
        return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    def _convert_version_to_spoken(self, version_text: str, language: str) -> str:
        """Convert version number (e.g., '3.14.159') to spoken form."""
        from revo_norm.normalizer_en import text_normalize as normalize_en
        from revo_norm.normalizer_ms import normalize_malay as normalize_ms

        if language in ("zh", "zh_my"):
            from revo_norm.num2word_zh import _DIGITS as _DIGITS_ZH
            parts = version_text.split(".")
            spoken_parts = [" ".join(_DIGITS_ZH.get(c, c) for c in p) for p in parts]
            return " 点 ".join(spoken_parts)
        else:
            normalize = normalize_ms if language == "ms" else normalize_en
            parts = version_text.split(".")
            spoken_parts = [normalize(p) for p in parts]
            return " point ".join(spoken_parts)

    def _convert_phone_to_spoken(self, phone_text: str, language: str) -> str:
        """Convert phone number to digit-by-digit spoken form."""
        from revo_norm.text_normalizer import _digit_word

        digits = re.sub(r"[\s\-+]", "", phone_text)
        return " ".join(_digit_word(d, language) for d in digits)

    def _convert_address_slash_to_spoken(self, address_text: str, language: str) -> str:
        """Convert address slash pattern to spoken form with digit-by-digit expansion."""
        from revo_norm.text_normalizer import _digit_word

        match = re.search(r"([A-Za-z]*)(\d+)\s*/\s*(\d+)([A-Za-z]+)?", address_text)
        if match:
            prefix = match.group(1)
            left_digits = " ".join(_digit_word(d, language) for d in match.group(2))
            right_digits = " ".join(_digit_word(d, language) for d in match.group(3))
            right_suffix = match.group(4) or ""
            prefix_spoken = " ".join(prefix) + " " if prefix else ""
            suffix_spoken = " ".join(right_suffix) + " " if right_suffix else ""
            separator = "slash"
            slash_spoken = f"{prefix_spoken}{left_digits} {separator} {right_digits} {suffix_spoken}".strip()
            return re.sub(r"[A-Za-z]*\d+\s*/\s*\d+[A-Za-z]*", slash_spoken, address_text)
        return address_text

    def _convert_date_to_spoken(self, date_text: str, language: str) -> str:
        """Convert a date to spoken form."""
        # Import number normalizers
        from revo_norm.normalizer_en import text_normalize as normalize_en
        from revo_norm.normalizer_ms import normalize_malay as normalize_ms
        from revo_norm.normalizer_zh import text_normalize_zh as normalize_zh
        from revo_norm.normalizer_zh_my import text_normalize_zh_my as normalize_zh_my

        # Detect date format and extract components
        # Format 1: DD/MM/YYYY or MM/DD/YYYY
        slash_match = re.match(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", date_text)
        if slash_match:
            day, month, year = slash_match.groups()
            if self._is_chinese(language):
                return self._date_to_chinese(slash_match, type="DMY")
            # Try to determine if DD/MM or MM/DD (assume DD/MM if day > 12)
            if int(day) > 12:
                # DD/MM format
                if language == "en":
                    day_spoken = normalize_en(day)
                    # Simple month name mapping
                    months = {
                        "01": "January",
                        "02": "February",
                        "03": "March",
                        "04": "April",
                        "05": "May",
                        "06": "June",
                        "07": "July",
                        "08": "August",
                        "09": "September",
                        "10": "October",
                        "11": "November",
                        "12": "December",
                    }
                    month_spoken = months.get(month, normalize_en(month))
                    year_spoken = normalize_en(year)
                    return f"{day_spoken} of {month_spoken} {year_spoken}"
                else:
                    day_spoken = normalize_ms(day)
                    months_ms = {
                        "01": "Januari",
                        "02": "Februari",
                        "03": "Mac",
                        "04": "April",
                        "05": "Mei",
                        "06": "Jun",
                        "07": "Julai",
                        "08": "Ogos",
                        "09": "September",
                        "10": "Oktober",
                        "11": "November",
                        "12": "Disember",
                    }
                    month_spoken = months_ms.get(month, normalize_ms(month))
                    year_spoken = normalize_ms(year)
                    return f"{day_spoken} {month_spoken} {year_spoken}"
            else:
                # MM/DD format (or ambiguous)
                if language == "en":
                    months = {
                        "01": "January",
                        "02": "February",
                        "03": "March",
                        "04": "April",
                        "05": "May",
                        "06": "June",
                        "07": "July",
                        "08": "August",
                        "09": "September",
                        "10": "October",
                        "11": "November",
                        "12": "December",
                    }
                    month_spoken = months.get(month, normalize_en(month))
                    day_spoken = normalize_en(day)
                    year_spoken = normalize_en(year)
                    return f"{month_spoken} {day_spoken}, {year_spoken}"
                else:
                    months_ms = {
                        "01": "Januari",
                        "02": "Februari",
                        "03": "Mac",
                        "04": "April",
                        "05": "Mei",
                        "06": "Jun",
                        "07": "Julai",
                        "08": "Ogos",
                        "09": "September",
                        "10": "Oktober",
                        "11": "November",
                        "12": "Disember",
                    }
                    month_spoken = months_ms.get(month, normalize_ms(month))
                    day_spoken = normalize_ms(day)
                    year_spoken = normalize_ms(year)
                    return f"{month_spoken} {day_spoken}, {year_spoken}"

        # Format 2: YYYY-MM-DD
        dash_match = re.match(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", date_text)
        if dash_match:
            year, month, day = dash_match.groups()
            if self._is_chinese(language):
                return self._date_to_chinese(dash_match, type="YMD")
            if language == "en":
                months = {
                    "01": "January",
                    "02": "February",
                    "03": "March",
                    "04": "April",
                    "05": "May",
                    "06": "June",
                    "07": "July",
                    "08": "August",
                    "09": "September",
                    "10": "October",
                    "11": "November",
                    "12": "December",
                }
                month_spoken = months.get(month.zfill(2), normalize_en(month))
                day_spoken = normalize_en(day)
                year_spoken = normalize_en(year)
                # Add ordinal suffix
                ordinal_suffix = self._get_ordinal_suffix(int(day))
                return f"{month_spoken} the {day_spoken}{ordinal_suffix}, {year_spoken}"
            else:
                months_ms = {
                    "01": "Januari",
                    "02": "Februari",
                    "03": "Mac",
                    "04": "April",
                    "05": "Mei",
                    "06": "Jun",
                    "07": "Julai",
                    "08": "Ogos",
                    "09": "September",
                    "10": "Oktober",
                    "11": "November",
                    "12": "Disember",
                }
                month_spoken = months_ms.get(month.zfill(2), normalize_ms(month))
                day_spoken = normalize_ms(day)
                year_spoken = normalize_ms(year)
                return f"{day_spoken} {month_spoken} {year_spoken}"

        # Format 3 & 4: Month name formats (handled by regex groups)
        # These are already in spoken format mostly, just normalize numbers
        # The normalizer will handle them in the basic phase

        # Fallback: Let basic normalizer handle it
        if language =="en":
            return normalize_en(date_text)
        elif language =="zh":
            return normalize_zh(date_text)
        elif language == "zh_my":
            return normalize_zh_my(date_text)
        else:
            return normalize_ms(date_text)

    def _convert_time_to_spoken(self, time_text: str, language: str) -> str:
        """Convert a time to spoken form."""
        from revo_norm.normalizer_en import text_normalize as normalize_en
        from revo_norm.normalizer_ms import normalize_malay as normalize_ms
        from revo_norm.normalizer_zh import text_normalize_zh as normalize_zh
        from revo_norm.normalizer_zh_my import text_normalize_zh_my as normalize_zh_my

        # Parse time format
        # HH:MM AM/PM or HH:MM:SS
        time_match = re.match(
            r"\b(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.|pagi|petang|malam|tengah\s+hari)?",
            time_text,
            re.IGNORECASE,
        )
        if time_match:
            hour = time_match.group(1)
            minute = time_match.group(2)
            second = time_match.group(3)
            ampm = time_match.group(4)

            if self._is_chinese(language):
                return self._time_to_chinese(language, hour, minute, second, ampm)

            if language == "en":
                hour_spoken = normalize_en(hour)
                minute_spoken = normalize_en(minute)
                result = f"{hour_spoken} {minute_spoken}"

                if second:
                    second_spoken = normalize_en(second)
                    result += f" {second_spoken}"

                if ampm:
                    ampm_clean = ampm.replace(".", "").lower()
                    if ampm_clean == "am":
                        result += " a m"
                    elif ampm_clean == "pm":
                        result += " p m"

                return result
            else:
                hour_spoken = normalize_ms(hour)
                minute_spoken = normalize_ms(minute)
                result = f"{hour_spoken} {minute_spoken}"

                if second:
                    second_spoken = normalize_ms(second)
                    result += f" {second_spoken}"

                if ampm:
                    ampm_clean = ampm.replace(".", "").lower().strip()
                    if ampm_clean in ("am", "pagi"):
                        result += " pagi"
                    elif ampm_clean in ("pm", "petang"):
                        result += " petang"
                    elif ampm_clean == "malam":
                        result += " malam"
                    elif ampm_clean.startswith("tengah"):
                        result += " tengah hari"

                return result

        # Fallback: Let basic normalizer handle it
        if language == "en":
            return normalize_en(time_text)
        elif language == "zh":
            return normalize_zh(time_text)
        elif language == "zh_my":
            return normalize_zh_my(time_text)
        else:
            return normalize_ms(time_text)

    def _convert_currency_to_spoken(self, currency_text: str, language: str) -> str:
        """Convert a currency amount to spoken form."""
        from revo_norm.currency_utils import (
            CURRENCY_B_SUFFIX_PATTERN,
            CURRENCY_K_SUFFIX_PATTERN,
            CURRENCY_M_SUFFIX_PATTERN,
            CURRENCY_T_SUFFIX_PATTERN,
            expand_currency_b_suffix,
            expand_currency_k_suffix,
            expand_currency_m_suffix,
            expand_currency_t_suffix,
        )
        from revo_norm.num2word_ms import to_cardinal as num2word

        # Initialize inflect engine for English number-to-words conversion
        _inflect_engine = inflect.engine()

        # First, expand suffixes if present (order matters: T → B → M → K)
        # RM1T → RM1000000000000
        # RM1B → RM1000000000
        # RM1M → RM1000000
        # RM30K → RM30000
        expanded = CURRENCY_T_SUFFIX_PATTERN.sub(
            lambda m: expand_currency_t_suffix(m), currency_text
        )
        expanded = CURRENCY_B_SUFFIX_PATTERN.sub(lambda m: expand_currency_b_suffix(m), expanded)
        expanded = CURRENCY_M_SUFFIX_PATTERN.sub(lambda m: expand_currency_m_suffix(m), expanded)
        expanded = CURRENCY_K_SUFFIX_PATTERN.sub(lambda m: expand_currency_k_suffix(m), expanded)

        # Parse the currency amount
        # Pattern: (RM|USD|EUR|GBP|MYR|$|£|€) + optional space + amount
        currency_match = re.match(
            r"(?<!\w)(RM|USD|EUR|GBP|MYR|\$|£|€)(?:\s?)([\d,]+(?:[\.,]\d+)?)",
            expanded,
            re.IGNORECASE,
        )

        if not currency_match:
            # Fallback: return original text
            return currency_text

        symbol = currency_match.group(1).upper()
        amount_str = currency_match.group(2).replace(",", "")

        # Map currency symbol to spoken form and units
        currency_names = {
            "RM": ("ringgit", "sen"),
            "MYR": ("ringgit", "sen"),
            "USD": ("dollar", "cents"),
            "$": ("dollar", "cents"),
            "EUR": ("euro", "cents"),
            "€": ("euro", "cents"),
            "GBP": ("pound", "pence"),
            "£": ("pound", "pence"),
        }

        unit_main, unit_sub = currency_names.get(symbol, (symbol.lower(), "cents"))

        # Chinese: delegate to Chinese currency converter
        if self._is_chinese(language):
            if language == "zh":
                from revo_norm.normalizer_zh import text_normalize_zh
                return text_normalize_zh(expanded)
            elif language == "zh_my":
                from revo_norm.normalizer_zh_my import text_normalize_zh_my
                return text_normalize_zh_my(expanded)

        # Handle decimal amounts
        if "." in amount_str:
            whole, frac = amount_str.split(".", 1)
            # Pad to 2 digits for cents (e.g., "5" → "50" for 0.50, "1" → "10" for 0.10)
            if len(frac) == 1:
                frac = frac + "0"
            # Limit to 2 digits (ignore micro-decimals)
            frac = frac[:2]
            if frac:
                if language == "en":
                    # Use inflect for whole numbers (e.g., "10000" → "ten thousand")
                    whole_spoken = _inflect_engine.number_to_words(int(whole))
                    # Treat fraction as whole number (e.g., "50" → "fifty")
                    frac_spoken = _inflect_engine.number_to_words(int(frac))
                    # Skip main unit if whole part is 0 (e.g., $0.50 → "fifty cents", not "zero dollar fifty cents")
                    if whole == "0":
                        return f"{frac_spoken} {unit_sub}"
                    return f"{whole_spoken} {unit_main} {frac_spoken} {unit_sub}"
                else:
                    whole_spoken = num2word(int(whole))
                    # Treat fraction as whole number in Malay (e.g., "50" → "lima puluh")
                    frac_spoken = num2word(int(frac))
                    # Skip main unit if whole part is 0 (e.g., RM0.50 → "lima puluh sen", not "kosong ringgit lima puluh sen")
                    if whole == "0":
                        return f"{frac_spoken} {unit_sub}"
                    return f"{whole_spoken} {unit_main} {frac_spoken} {unit_sub}"
            else:
                # Trailing decimal only, treat as whole number
                amount_str = whole

        # Whole number amount
        if language == "en":
            # Use inflect for whole numbers (e.g., "10000" → "ten thousand")
            amount_spoken = _inflect_engine.number_to_words(int(amount_str))
        else:
            # Use num2word for proper Malay number conversion
            amount_spoken = num2word(int(amount_str))

        return f"{amount_spoken} {unit_main}"
