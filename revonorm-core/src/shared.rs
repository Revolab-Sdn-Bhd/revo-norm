//! shared — port of revo_norm/shared_features.py + the shared-feature
//! entity types from entity_extractor.py (milestone 3).
//!
//! Two surfaces:
//!   1. Text passes that run BEFORE the language normalizer:
//!      measurements (distance/volume/weight/duration/area).
//!   2. Entity types with spoken converters: TEMPERATURE, FRACTION,
//!      X_KALI, HIJRI, HARI_BULAN, IC (extracted like milestone-2 types).

use fancy_regex::Regex;
use std::sync::LazyLock;

use crate::langpack::get_pack;
use crate::num2word::to_cardinal;

// --- measurement patterns (shared_features.py) ----------------------------
static RE_DISTANCE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b(-?\d+(?:[\.,]\d+)?)\s*(km|m|cm|mm|ft|in|yd|mi|batu|kaki|inci)\b").unwrap()
});
static RE_VOLUME: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?i)\b(-?\d+(?:[\.,]\d+)?)\s*(ml|l|gal)\b").unwrap());
static RE_WEIGHT: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?i)\b(-?\d+(?:[\.,]\d+)?)\s*(kg|g|mg|lb|oz)\b").unwrap());
static RE_DURATION: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b(\d+)\s*(jam|minit|saat|hours?|minutes?|seconds?)\b").unwrap()
});
static RE_AREA: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?i)\b(-?\d+(?:[\.,]\d+)?)\s*(sq\s+ft|sqft)\b").unwrap());

// --- shared-feature entity patterns (entity_extractor.py) -----------------
static RE_TEMPERATURE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<![A-Za-z0-9_])(-?\d+(?:[\.,]\d+)?)\s*(?:°)?([CFK])(?![A-Za-z0-9_])").unwrap()
});
static RE_FRACTION: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<![\d/])(\d+)\s*/\s*(\d+)(?![/\d])").unwrap());
static RE_X_KALI: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\b(\d+)\s*[xX]\b").unwrap());
static RE_IC: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b(\d{6})-?(\d{2})-?(\d{4})\b").unwrap());
static RE_HARI_BULAN: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b([1-9]|[12]\d|3[01])\s*[Hh][Bb]\b").unwrap());
static RE_HIJRI: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b(\d{3,4})\s*[Hh]\b").unwrap());

/// Measurements pass — before the language normalizer so "5km" never
/// becomes "lima K M". Values spoken via the malay cardinal engine (ms
/// milestone); units via the pack tables.
pub fn normalize_measurements(text: &str, language: &str) -> String {
    let pack = get_pack(language);
    let speak = |v: &str| -> String {
        let cleaned = v.replace(',', ".");
        if let Ok(n) = cleaned.parse::<u128>() {
            to_cardinal(n)
        } else if let Ok(f) = cleaned.parse::<f64>() {
            // decimals: whole koma digits
            let s = format!("{f}");
            if let Some((w, frac)) = s.split_once('.') {
                let digits: String = frac.chars().map(|d| to_cardinal(d.to_digit(10).unwrap_or(0) as u128)).collect::<Vec<_>>().join(" ");
                return format!("{} perpuluhan {digits}", to_cardinal(w.parse().unwrap_or(0)));
            }
            to_cardinal(f as u128)
        } else {
            v.to_string()
        }
    };

    let sub_units = |re: &Regex, table: &std::collections::HashMap<String, String>, out: String| -> String {
        re.replace_all(&out, |c: &fancy_regex::Captures<str>| {
            let unit = c.get(2).map(|m| m.as_str().to_lowercase()).unwrap_or_default();
            match table.get(&unit) {
                Some(spoken) => format!("{} {spoken}", speak(c.get(1).map(|m| m.as_str()).unwrap_or("0"))),
                None => c.get(0).map(|m| m.as_str().to_string()).unwrap_or_default(),
            }
        })
        .into_owned()
    };

    let out = sub_units(&RE_DISTANCE, &pack.distance_units, text.to_string());
    let out = sub_units(&RE_VOLUME, &pack.volume_units, out);
    let out = sub_units(&RE_WEIGHT, &pack.weight_units, out);
    let out = sub_units(&RE_DURATION, &pack.duration_units, out);
    sub_units(&RE_AREA, &pack.area_units, out)
}

// --- spoken converters for shared-feature entities -------------------------

pub fn spoken_temperature(text: &str, language: &str) -> String {
    let pack = get_pack(language);
    if let Ok(Some(c)) = RE_TEMPERATURE.captures(text) {
        let value = c.get(1).map(|m| m.as_str()).unwrap_or("0").replace(',', ".");
        let unit = c.get(2).map(|m| m.as_str().to_lowercase()).unwrap_or_default();
        if let Some(spoken) = pack.temperature_units.get(&unit) {
            if let Some((w, frac)) = value.split_once('.') {
                let digits: String = frac.chars().map(|d| to_cardinal(d.to_digit(10).unwrap_or(0) as u128)).collect::<Vec<_>>().join(" ");
                return format!("{} perpuluhan {digits} {spoken}", to_cardinal(w.parse().unwrap_or(0)));
            }
            return format!("{} {spoken}", to_cardinal(value.parse().unwrap_or(0)));
        }
    }
    text.to_string()
}

pub fn spoken_fraction(text: &str) -> String {
    if let Ok(Some(c)) = RE_FRACTION.captures(text) {
        let n = c.get(1).map(|m| m.as_str()).unwrap_or("0");
        let d = c.get(2).map(|m| m.as_str()).unwrap_or("0");
        return format!("{} per {}", to_cardinal(n.parse().unwrap_or(0)), to_cardinal(d.parse().unwrap_or(0)));
    }
    text.to_string()
}

pub fn spoken_x_kali(text: &str) -> String {
    if let Ok(Some(c)) = RE_X_KALI.captures(text) {
        let n = c.get(1).map(|m| m.as_str()).unwrap_or("0");
        return format!("{} kali", to_cardinal(n.parse().unwrap_or(0)));
    }
    text.to_string()
}

pub fn spoken_ic(text: &str) -> String {
    let pack = get_pack("ms");
    text.chars()
        .filter(|c| c.is_ascii_digit())
        .map(|d| pack.speak_digit(d))
        .collect::<Vec<_>>()
        .join(" ")
}

pub fn spoken_hari_bulan(text: &str) -> String {
    if let Ok(Some(c)) = RE_HARI_BULAN.captures(text) {
        let day = c.get(1).map(|m| m.as_str()).unwrap_or("0");
        return format!("{} hari bulan", to_cardinal(day.parse().unwrap_or(0)));
    }
    text.to_string()
}

pub fn spoken_hijri(text: &str) -> String {
    let pack = get_pack("ms");
    if let Ok(Some(c)) = RE_HIJRI.captures(text) {
        let year = c.get(1).map(|m| m.as_str()).unwrap_or("0");
        let digits: String = year
            .chars()
            .map(|d| pack.speak_digit(d))
            .collect::<Vec<_>>()
            .join(" ");
        return format!("{digits} Hijri");
    }
    text.to_string()
}

/// Patterns for the shared-feature entity types, exposed for the entity
/// module's extraction loop (python pattern order: after DATE/TIME come
/// TEMPERATURE, FRACTION, X_KALI, IC, HARI_BULAN, HIJRI).
pub fn shared_pattern(tag: &str) -> Option<&'static Regex> {
    Some(match tag {
        "TEMPERATURE" => &RE_TEMPERATURE,
        "FRACTION" => &RE_FRACTION,
        "X_KALI" => &RE_X_KALI,
        "IC" => &RE_IC,
        "HARI_BULAN" => &RE_HARI_BULAN,
        "HIJRI" => &RE_HIJRI,
        _ => return None,
    })
}

pub fn shared_spoken(tag: &str, text: &str, language: &str) -> Option<String> {
    Some(match tag {
        "TEMPERATURE" => spoken_temperature(text, language),
        "FRACTION" => spoken_fraction(text),
        "X_KALI" => spoken_x_kali(text),
        "IC" => spoken_ic(text),
        "HARI_BULAN" => spoken_hari_bulan(text),
        "HIJRI" => spoken_hijri(text),
        _ => return None,
    })
}
