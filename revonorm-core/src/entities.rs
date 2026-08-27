//! entities — port of revo_norm/entity_extractor.py's extract→placeholder→
//! restore skeleton (milestone 2). Entity types whose spoken conversion is a
//! shared feature (fractions, hijri, hari-bulan, temperature, x-kali, IC)
//! land with milestone 3; the patterns here are Python's, verbatim.

use fancy_regex::Regex;
use std::sync::LazyLock;

use crate::langpack::get_pack;

/// Language-aware cardinal dispatch.
fn cardinal_for(n: u128, language: &str) -> String {
    match language {
        "id" => crate::num2word::to_cardinal_id(n),
        "en" => crate::num2word_en::to_cardinal_en(n),
        _ => crate::num2word::to_cardinal(n),
    }
}


#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub enum EntityType {
    Url,
    Email,
    Phone,
    Version,
    Currency,
    Date,
    Time,
    // milestone 3: shared-feature entity types
    Temperature,
    AddressSlash,
    Fraction,
    XKali,
    Ic,
    HariBulan,
    Hijri,
}

impl EntityType {
    pub fn tag(&self) -> &'static str {
        match self {
            EntityType::Url => "URL",
            EntityType::Email => "EMAIL",
            EntityType::Phone => "PHONE",
            EntityType::Version => "VERSION",
            EntityType::Currency => "CURRENCY",
            EntityType::Date => "DATE",
            EntityType::Time => "TIME",
            EntityType::Temperature => "TEMPERATURE",
            EntityType::AddressSlash => "ADDRESS_SLASH",
            EntityType::Fraction => "FRACTION",
            EntityType::XKali => "X_KALI",
            EntityType::Ic => "IC",
            EntityType::HariBulan => "HARI_BULAN",
            EntityType::Hijri => "HIJRI",
        }
    }
}

/// Parse a pybind tag string back to its EntityType.
pub fn entity_kind_from_tag(tag: &str) -> EntityType {
    match tag {
        "URL" => EntityType::Url,
        "EMAIL" => EntityType::Email,
        "PHONE" => EntityType::Phone,
        "VERSION" => EntityType::Version,
        "CURRENCY" => EntityType::Currency,
        "DATE" => EntityType::Date,
        "TIME" => EntityType::Time,
        "TEMPERATURE" => EntityType::Temperature,
        "ADDRESS_SLASH" => EntityType::AddressSlash,
        "FRACTION" => EntityType::Fraction,
        "X_KALI" => EntityType::XKali,
        "IC" => EntityType::Ic,
        "HARI_BULAN" => EntityType::HariBulan,
        "HIJRI" => EntityType::Hijri,
        _ => EntityType::Url,
    }
}

/// Speak one entity (pybind surface: tag + raw text). Err on unknown
/// language so FFI callers get a clean error, not a panic.
pub fn speak_entity(kind: EntityType, text: &str, language: &str) -> Result<String, String> {
    if crate::langpack::try_get_pack(language).is_none() {
        let langs = crate::langpack::supported_languages().join(", ");
        return Err(format!(
            "Unsupported language: '{language}' (expected one of ({langs}))"
        ));
    }
    let e = Entity {
        kind,
        text: text.to_string(),
        placeholder_id: 0,
    };
    Ok(convert_to_spoken(&e, language))
}

pub struct Entity {
    pub kind: EntityType,
    pub text: String,
    pub placeholder_id: usize,
}

static RE_URL: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?:https?://|ftp://|www\.)[^\s]+|\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/[^\s]*)?|\b[A-Za-z0-9-]+\.[A-Za-z]{2,}(?:/[^\s]*)?").unwrap()
});
static RE_EMAIL: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b").unwrap()
});
static RE_PHONE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?<!\w)(?:\+?6?01\d[-\s]?\d{3,4}[-\s]?\d{4}|\+?6?0\d[-\s]?\d{4}[-\s]?\d{4}|1[-\s]?[348]00[-\s]?\d{2}[-\s]?\d{4}|154\d{2})(?!\w)").unwrap()
});
static RE_VERSION: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b(?!\d{4}\.\d{1,2}\.\d{1,2}\b)(\d+)(?:\.\d+){2,}\b").unwrap());
static RE_CURRENCY: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<!\w)(RM|Rp|USD|EUR|GBP|MYR|IDR|\$|£|€)(?:\s?)([\d,]+(?:[\.,]\d{1,2})?)(?:[KMBT])?\b").unwrap()
});
static RE_DATE: LazyLock<Regex> = LazyLock::new(|| {
    let patterns = [
        r"(?<![A-Za-z0-9_])\d{1,2}/\d{1,2}/\d{4}(?![A-Za-z0-9_])",
        r"(?<![A-Za-z0-9_])\d{4}-\d{1,2}-\d{1,2}(?![A-Za-z0-9_])",
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b",
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b",
    ];
    Regex::new(&patterns.iter().map(|p| format!("(?:{p})")).collect::<Vec<_>>().join("|")).unwrap()
});
static RE_ADDRESS_SLASH: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b(?:Jalan|Lorong|Taman|Bukit|Kampung|Tingkat|Lintang|Pesisir|Persiaran|Lebuh|Medan|Lengkung|Halaman)\s+(?:\S+\s+)?(\d+)\s*/\s*(\d+)\b|\b(?:Jalan|Lorong|Taman|Bukit|Kampung|Tingkat|Lintang|Pesisir|Persiaran|Lebuh|Medan|Lengkung|Halaman)\s+([A-Za-z]*\d+)\s*/\s*(\d+)\b").unwrap()
});
static RE_TIME: LazyLock<Regex> = LazyLock::new(|| {
    let patterns = [
        r"\b\d{1,2}:\d{2}\s*(?:pagi|petang|siang|sore|malam|tengah\s+hari)\b",
        r"\b\d{1,2}:\d{2}\s*(?:am|pm|a\.m\.|p\.m\.)?(?![A-Za-z0-9_])",
        r"\b\d{1,2}:\d{2}:\d{2}\b",
    ];
    Regex::new(&format!("(?i){}", patterns.iter().map(|p| format!("(?:{p})")).collect::<Vec<_>>().join("|"))).unwrap()
});

/// Python's extraction order (most specific first).
const ORDER: [EntityType; 14] = [
    EntityType::Email,
    EntityType::Url,
    EntityType::Phone,
    EntityType::Version,
    EntityType::Currency,
    EntityType::Date,
    EntityType::Time,
    EntityType::Temperature,
    EntityType::AddressSlash, // python: before FRACTION so addresses win
    EntityType::Fraction,
    EntityType::XKali,
    EntityType::Ic,
    EntityType::HariBulan,
    EntityType::Hijri,
];

fn pattern_for(kind: EntityType) -> Option<&'static Regex> {
    let re = match kind {
        EntityType::Url => &RE_URL,
        EntityType::Email => &RE_EMAIL,
        EntityType::Phone => &RE_PHONE,
        EntityType::Version => &RE_VERSION,
        EntityType::Currency => &RE_CURRENCY,
        EntityType::Date => &RE_DATE,
        EntityType::Time => &RE_TIME,
        EntityType::AddressSlash => &RE_ADDRESS_SLASH,
        other => return crate::shared::shared_pattern(other.tag()),
    };
    Some(re)
}

/// Extract entities and replace with `<<<TYPE_N>>>` placeholders.
pub fn extract(text: &str) -> (String, Vec<Entity>) {
    extract_gated(text, &crate::options::Options::default())
}

/// Feature -> entity types that only extract when the feature is on
/// (python always_extract/speak_entities gating). URL/EMAIL/PHONE/
/// VERSION/CURRENCY extract unconditionally.
fn feature_for(kind: EntityType) -> Option<&'static str> {
    match kind {
        EntityType::Url
        | EntityType::Email
        | EntityType::Phone
        | EntityType::Version
        | EntityType::Currency => None,
        EntityType::Date => Some("dates"),
        EntityType::Time => Some("times"),
        EntityType::Temperature => Some("temperature"),
        EntityType::AddressSlash => Some("fractions"),
        EntityType::Fraction => Some("fractions"),
        EntityType::XKali => Some("x_kali"),
        EntityType::Ic => Some("ic"),
        EntityType::HariBulan => Some("hari_bulan"),
        EntityType::Hijri => Some("hijri"),
    }
}

/// Extraction honoring feature gates. DATE/TIME are ALWAYS extracted
/// (python protects them from the language normalizer regardless) but only
/// spoken when their feature is on; other gated types are never claimed
/// when off, so their text flows to the language normalizer untouched
/// (python parity: minimal/basic leave "25C" to the mixed-alnum pass).
pub fn extract_gated(text: &str, options: &crate::options::Options) -> (String, Vec<Entity>) {
    let mut entities = Vec::new();
    let mut protected = text.to_string();
    let mut next_id = 1usize;
    for kind in ORDER {
        if feature_for(kind).is_some_and(|f| !options.is_enabled(f))
            && !matches!(kind, EntityType::Date | EntityType::Time)
        {
            continue;
        }
        let Some(re) = pattern_for(kind) else { continue };
        let mut out = String::with_capacity(protected.len());
        let mut last = 0usize;
        for m in re.find_iter(&protected) {
            let Ok(m) = m else { break };
            out.push_str(&protected[last..m.start()]);
            out.push_str(&format!("<<<{}_{next_id}>>>", kind.tag()));
            entities.push(Entity {
                kind,
                text: m.as_str().to_string(),
                placeholder_id: next_id,
            });
            next_id += 1;
            last = m.end();
        }
        out.push_str(&protected[last..]);
        protected = out;
    }
    (protected, entities)
}

/// Restore placeholders to spoken form (reverse id order, like python).
pub fn restore(text: &str, entities: &[Entity], language: &str) -> String {
    restore_gated(text, entities, language, &crate::options::Options::default())
}

/// Restore honoring python's speak_entities: DATE/TIME are always extracted
/// (protected) but only converted to speech when their feature is on;
/// otherwise they restore as the original raw text.
pub fn restore_gated(
    text: &str,
    entities: &[Entity],
    language: &str,
    options: &crate::options::Options,
) -> String {
    let mut result = text.to_string();
    for e in entities.iter().rev() {
        let ph = format!("<<<{}_{}>>>", e.kind.tag(), e.placeholder_id);
        if let Some(pos) = result.find(&ph) {
            let speak = match feature_for(e.kind) {
                Some(f) if matches!(e.kind, EntityType::Date | EntityType::Time) => {
                    options.is_enabled(f)
                }
                _ => true,
            };
            let spoken = if speak {
                convert_to_spoken(e, language)
            } else {
                e.text.clone()
            };
            result.replace_range(pos..pos + ph.len(), &spoken);
        }
    }
    result
}

fn convert_to_spoken(e: &Entity, language: &str) -> String {
    if e.kind == EntityType::AddressSlash {
        // python: prefix kept, digits spoken, "/" -> " slash "
        let re = fancy_regex::Regex::new(r"(?i)\b((?:Jalan|Lorong|Taman|Bukit|Kampung|Tingkat|Lintang|Pesisir|Persiaran|Lebuh|Medan|Lengkung|Halaman)\s+)(?:\S+\s+)?([A-Za-z]*)(\d+)\s*/\s*(\d+)").unwrap();
        if let Ok(Some(c)) = re.captures(&e.text) {
            let pack = get_pack(language);
            let prefix = c.get(1).map(|m| m.as_str()).unwrap_or("");
            let letters = c.get(2).map(|m| m.as_str()).unwrap_or("");
            let left = c.get(3).map(|m| m.as_str()).unwrap_or("0");
            let right = c.get(4).map(|m| m.as_str()).unwrap_or("0");
            let speak = |s: &str| -> String {
                s.chars().map(|d| if d.is_ascii_digit() { pack.speak_digit(d) } else { d.to_uppercase().to_string() }).collect::<Vec<_>>().join(" ")
            };
            let letters_spoken: String = letters.chars().map(|c| c.to_uppercase().to_string()).collect::<Vec<_>>().join(" ");
            let mut out = format!("{prefix}{letters_spoken} {}", speak(left));
            out.push_str(" slash ");
            out.push_str(&speak(right));
            return squash_spaces(&out);
        }
        return e.text.clone();
    }
    if let Some(spoken) = crate::shared::shared_spoken(e.kind.tag(), &e.text, language) {
        return spoken;
    }
    match e.kind {
        EntityType::Phone => {
            // python: strip space/-/+ then speak every digit
            let pack = get_pack(language);
            e.text
                .chars()
                .filter(|c| c.is_ascii_digit())
                .map(|d| pack.speak_digit(d))
                .collect::<Vec<_>>()
                .join(" ")
        }
        EntityType::Currency => spoken_currency(&e.text, language),
        EntityType::Time => spoken_time(&e.text, language),
        EntityType::Url => spoken_url(&e.text, language),
        EntityType::Email => spoken_email(&e.text, language),
        EntityType::Version => spoken_version(&e.text, language),
        EntityType::Date => spoken_date(&e.text, language),
        // unreachable: shared_spoken handled these above
        EntityType::Temperature
        | EntityType::AddressSlash
        | EntityType::Fraction
        | EntityType::XKali
        | EntityType::Ic
        | EntityType::HariBulan
        | EntityType::Hijri => e.text.clone(),
    }
}

/// python url_to_spoken (latin branch — zh arrives with the zh milestone).
fn spoken_url(url: &str, language: &str) -> String {
    let pack = get_pack(language);
    let zh = matches!(language, "zh" | "zh_my");
    let mut spoken = url.to_string();
    if zh {
        // python zh: protocol + 冒号斜杠斜杠 (zh) / 冒号 slash slash (zh_my),
        // 点, 斜杠, 杠, 问号, 等于, digits spoken with zh digits.
        let sep = if language == "zh" { "冒号斜杠斜杠" } else { "冒号 slash slash " };
        if let Some((protocol, _)) = spoken.clone().split_once("://") {
            let protocol_spoken: String = protocol.chars().map(|c| c.to_string()).collect::<Vec<_>>().join(" ");
            spoken = spoken.replace(&format!("{protocol}://"), &format!("{protocol_spoken} {sep}"));
        }
        if let Ok(re) = fancy_regex::Regex::new(r"www\.?") {
            spoken = re.replace_all(&spoken, "w w w 点 ").into_owned();
        }
        spoken = spoken.replace('.', "点");
        spoken = spoken.replace('/', "斜杠");
        spoken = spoken.replace('-', "杠");
        spoken = spoken.replace('?', " 问号 ").replace('=', " 等于 ");
        spoken = spoken.replace('&', " 和 ").replace('*', " 星号 ");
        if let Ok(re) = fancy_regex::Regex::new(r"\d+") {
            spoken = re
                .replace_all(&spoken, |c: &fancy_regex::Captures<str>| {
                    c[0].chars().map(|d| crate::normalize_zh::to_cardinal_zh(d.to_digit(10).unwrap_or(0) as u128)).collect::<Vec<_>>().join(" ")
                })
                .into_owned();
        }
        return squash_spaces(spoken.trim());
    }
    if let Some((protocol, _)) = spoken.clone().split_once("://") {
        let protocol_spoken: String = protocol.chars().map(|c| c.to_string()).collect::<Vec<_>>().join(" ");
        spoken = spoken.replace(
            &format!("{protocol}://"),
            &format!("{protocol_spoken} colon slash slash "),
        );
    }
    // www -> "w w w dot "
    if let Ok(re) = fancy_regex::Regex::new(r"www\.?") {
        spoken = re.replace_all(&spoken, "w w w dot ").into_owned();
    }
    // ports
    if let Ok(re) = fancy_regex::Regex::new(r":(\d+)") {
        spoken = re
            .replace_all(&spoken, |c: &fancy_regex::Captures<str>| {
                let digits: String = c[1].chars().map(|d| pack.speak_digit(d)).collect::<Vec<_>>().join(" ");
                format!(" colon {digits}")
            })
            .into_owned();
    }
    spoken = spoken.replace('.', " dot ");
    spoken = spoken.replace('/', " slash ");
    spoken = spoken.replace('-', " dash ");
    spoken = spoken.replace('?', " question mark ");
    spoken = spoken.replace('=', " equals ");
    spoken = spoken.replace('&', " and ");
    if language == "en" || language == "ms" {
        spoken = spoken.replace('*', " ");
        spoken = spoken.replace('!', "");
    } else {
        spoken = spoken.replace('*', " star ");
    }
    // digits word-by-word
    if let Ok(re) = fancy_regex::Regex::new(r"\d+") {
        spoken = re
            .replace_all(&spoken, |c: &fancy_regex::Captures<str>| {
                c[0].chars().map(|d| pack.speak_digit(d)).collect::<Vec<_>>().join(" ")
            })
            .into_owned();
    }
    squash_spaces(&spoken)
}

/// python email_to_spoken (latin branch).
fn spoken_email(email: &str, language: &str) -> String {
    let pack = get_pack(language);
    let zh = matches!(language, "zh" | "zh_my");
    if zh {
        // python email_to_spoken zh branch: 艾特/点/下划线/加/杠, then digits
        let mut s = email.replace('@', "艾特");
        s = s.replace('.', "点");
        s = s.replace('_', "下划线");
        s = s.replace('+', "加");
        s = s.replace('-', "杠");
        if let Ok(re) = fancy_regex::Regex::new(r"\d+") {
            s = re
                .replace_all(&s, |c: &fancy_regex::Captures<str>| {
                    c[0].chars().map(|d| pack.speak_digit(d)).collect::<Vec<_>>().join(" ")
                })
                .into_owned();
        }
        return squash_spaces(&s);
    }
    let spoken = email.replace('@', " at ");
    let mut spoken = spoken.replace('.', " dot ");
    spoken = spoken.replace('_', " underscore ");
    spoken = spoken.replace('+', " plus ");
    spoken = spoken.replace('-', " dash ");
    // insert space at letter<->digit boundaries
    if let Ok(re) = fancy_regex::Regex::new(r"(?<=[a-zA-Z])(?=\d)|(?<=\d)(?=[a-zA-Z])") {
        spoken = re.replace_all(&spoken, " ").into_owned();
    }
    if let Ok(re) = fancy_regex::Regex::new(r"\d+") {
        spoken = re
            .replace_all(&spoken, |c: &fancy_regex::Captures<str>| {
                c[0].chars().map(|d| pack.speak_digit(d)).collect::<Vec<_>>().join(" ")
            })
            .into_owned();
    }
    squash_spaces(&spoken)
}

/// python _convert_version_to_spoken (latin): each part spoken as a number,
/// joined with " point ".
fn spoken_version(version: &str, language: &str) -> String {
    version
        .split('.')
        .map(|p| cardinal_for(p.parse::<u128>().unwrap_or(0), language))
        .collect::<Vec<_>>()
        .join(" point ")
}

/// python _convert_date_to_spoken (ms branch): day month-name year, each as
/// cardinal words.
pub fn spoken_date(date: &str, language: &str) -> String {
    // Format 2 first (python order): YYYY-MM-DD dash form
    let ymd = fancy_regex::Regex::new(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b").unwrap();
    if let Ok(Some(c)) = ymd.captures(date) {
        let y: u128 = c.get(1).map(|m| m.as_str()).unwrap_or("0").parse().unwrap_or(0);
        let mo = c.get(2).map(|m| m.as_str()).unwrap_or("1");
        let d: u128 = c.get(3).map(|m| m.as_str()).unwrap_or("0").parse().unwrap_or(0);
        if matches!(language, "zh" | "zh_my") {
            let month = crate::normalize_zh::MONTHS_ZH
                .get(mo.trim_start_matches('0'))
                .cloned()
                .unwrap_or_else(|| mo.to_string());
            return format!(
                "{}年{month}月{}日",
                crate::normalize_zh::to_year_zh(y),
                crate::normalize_zh::to_cardinal_zh(d)
            );
        }
        let cardinal = |n: u128| cardinal_for(n, language);
        let month_name = get_pack(language)
            .month_names
            .get(mo.trim_start_matches('0'))
            .copied()
            .unwrap_or(mo);
        return format!("{} {month_name} {}", cardinal(d), cardinal(y));
    }
    // slash format DD/MM/YYYY (or MM/DD when month>12 — python swaps)
    let re = fancy_regex::Regex::new(r"(?<![A-Za-z0-9_])(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})(?![A-Za-z0-9_])").unwrap();
    let cardinal = |s: &str| cardinal_for(s.parse::<u128>().unwrap_or(0), language);
    if let Ok(Some(c)) = re.captures(date) {
        let mut day_str = c.get(1).map(|m| m.as_str()).unwrap_or("0").to_string();
        let mut month_str = c.get(2).map(|m| m.as_str()).unwrap_or("1").to_string();
        // MM/DD ambiguity: when "month" exceeds 12 the first field must be
        // the day (python's swap in normalize_date_dmy)
        if month_str.parse::<u32>().unwrap_or(0) > 12 && day_str.parse::<u32>().unwrap_or(0) <= 12 {
            std::mem::swap(&mut day_str, &mut month_str);
        }
        let day_num: u128 = day_str.parse().unwrap_or(0);
        let year_num: u128 = c.get(3).map(|m| m.as_str()).unwrap_or("0").parse().unwrap_or(0);
        if matches!(language, "zh" | "zh_my") {
            // python zh: '<year 年><month 数字>月<day cardinal>日'
            let czh = crate::normalize_zh::to_cardinal_zh;
            let month_num = &month_str;
            let month = crate::normalize_zh::MONTHS_ZH
                .get(month_num.trim_start_matches('0'))
                .cloned()
                .unwrap_or_else(|| month_num.to_string());
            return format!(
                "{}年{month}月{}日",
                crate::normalize_zh::to_year_zh(year_num),
                czh(day_num)
            );
        }
        if language == "en" {
            // python entity en: '<day cardinal> of <Month> <year>' with the
            // year rendered by the en bare-number rule (4-digit 1000-2099 ->
            // year style: 'twenty twenty-five').
            let month_num = &month_str;
            let month = get_pack(language)
                .month_names
                .get(month_num.trim_start_matches('0'))
                .copied()
                .unwrap_or(month_num);
            let year_spoken = if (1000..=2099).contains(&year_num) {
                crate::normalize_en::render_year(year_num)
            } else {
                crate::num2word_en::to_cardinal_en(year_num)
            };
            return format!(
                "{} of {month} {year_spoken}",
                crate::num2word_en::to_cardinal_en(day_num)
            );
        }
        let day = cardinal(&day_str);
        let year = cardinal(c.get(3).map(|m| m.as_str()).unwrap_or("0"));
        let month_num = &month_str;
        let month = get_pack(language)
            .month_names
            .get(month_num.trim_start_matches('0'))
            .copied()
            .unwrap_or(month_num);
        return format!("{day} {month} {year}");
    }
    date.to_string()
}

fn squash_spaces(text: &str) -> String {
    text.split_whitespace().collect::<Vec<_>>().join(" ")
}

/// python _convert_currency_to_spoken (ms branch): per-symbol unit names,
/// cents spoken as a padded 2-digit number, whole==0 skips the main unit.
/// python _convert_currency_to_spoken: per-symbol unit names from the pack,
/// cents spoken as a padded 2-digit number, whole==0 skips the main unit.
fn spoken_currency(text: &str, language: &str) -> String {
    let pack = get_pack(language);
    if matches!(language, "zh" | "zh_my") {
        // python delegates zh currency to normalizer_zh.normalize_currency:
        // cardinal + 令吉/美元/... + cardinal + 仙/分, joined without spaces
        let re = fancy_regex::Regex::new(
            r"(?i)(?<![A-Za-z0-9_])(\$|£|€|RM|MYR|USD|EUR|GBP)(?:\s?)([\d,]+(?:[\.,]\d{1,2})?)",
        )
        .unwrap();
        if let Ok(Some(c)) = re.captures(text) {
            let symbol = c[1].to_uppercase();
            let amount = c[2].replace(',', "");
            // zh_my uses colloquial currency words (美金/英磅/块 fallback);
            // zh uses 美元/英镑/分
            let (unit_main, unit_sub) = if language == "zh_my" {
                match symbol.as_str() {
                    "RM" | "MYR" => ("令吉", "仙"),
                    "$" | "USD" => ("美金", "仙"),
                    "£" | "GBP" => ("英磅", "仙"),
                    "€" | "EUR" => ("欧元", "仙"),
                    _ => ("块", "仙"),
                }
            } else {
                match symbol.as_str() {
                    "RM" | "MYR" => ("令吉", "仙"),
                    "$" | "USD" => ("美元", "分"),
                    "£" | "GBP" => ("英镑", "便士"),
                    "€" | "EUR" => ("欧元", "分"),
                    _ => ("元", "分"),
                }
            };
            let czh = crate::normalize_zh::to_cardinal_zh;
            if let Some((w, f_raw)) = amount.split_once('.') {
                let mut f = f_raw.to_string();
                while f.len() < 2 {
                    f.push('0');
                }
                let f = &f[..2];
                if f != "00" {
                    return format!("{}{unit_main}{}{unit_sub}", czh(w.parse().unwrap_or(0)), czh(f.parse().unwrap_or(0)));
                }
                return format!("{}{unit_main}", czh(w.parse().unwrap_or(0)));
            }
            return format!("{}{unit_main}", czh(amount.parse().unwrap_or(0)));
        }
        return text.to_string();
    }
    let cardinal = |n: u128| cardinal_for(n, language);
    let re = fancy_regex::Regex::new(
        r"(?i)(?<!\w)(RM|Rp|USD|EUR|GBP|MYR|IDR|\$|£|€)(?:\s?)([\d,]+(?:[\.,]\d{1,2})?)",
    )
    .unwrap();
    let Ok(Some(m)) = re.find(text) else {
        return text.to_string();
    };
    let Ok(Some(caps)) = re.captures(m.as_str()) else {
        return text.to_string();
    };
    let symbol = caps.get(1).map(|g| g.as_str().to_uppercase()).unwrap_or_default();
    let amount = caps
        .get(2)
        .map(|g| g.as_str().replace(',', ""))
        .unwrap_or_default();
    let default_units = match symbol.as_str() {
        "RM" | "MYR" => ("ringgit", "sen"),
        "RP" | "IDR" => ("rupiah", "sen"),
        "USD" | "$" => ("dollar", "cents"),
        "EUR" | "€" => ("euro", "cents"),
        "GBP" | "£" => ("pound", "pence"),
        _ => (&symbol[..], "cents"),
    };
    let (unit_main, unit_sub) = pack
        .currency_names
        .get(symbol.as_str())
        .copied()
        .unwrap_or(default_units);
    if let Some((whole, frac_raw)) = amount.split_once('.') {
        let mut frac = frac_raw.to_string();
        if frac.len() == 1 {
            frac.push('0');
        }
        let frac = &frac[..frac.len().min(2)];
        if !frac.is_empty() {
            let frac_spoken = cardinal(frac.parse::<u128>().unwrap_or(0));
            if whole == "0" {
                return format!("{frac_spoken} {unit_sub}");
            }
            return format!(
                "{} {unit_main} {frac_spoken} {unit_sub}",
                cardinal(whole.parse::<u128>().unwrap_or(0))
            );
        }
    }
    format!("{} {unit_main}", cardinal(amount.parse::<u128>().unwrap_or(0)))
}

fn spoken_time(text: &str, language: &str) -> String {
    // python _convert_time_to_spoken: hour minute [second] words + meridian;
    // minute always spoken. am->pagi both langs; pm->petang (ms) / sore (id).
    if matches!(language, "zh" | "zh_my") {
        // python _time_to_chinese: 下午/上午 + 时分, no spaces; pm by hour
        let re = fancy_regex::Regex::new(
            r"(?i)\b(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.|pagi|petang|siang|sore|malam|tengah\s+hari)?",
        )
        .unwrap();
        if let Ok(Some(c)) = re.captures(text) {
            let h: u32 = c.get(1).map(|m| m.as_str()).unwrap_or("0").parse().unwrap_or(0);
            let m: u32 = c.get(2).map(|m| m.as_str()).unwrap_or("0").parse().unwrap_or(0);
            let zh_my_variant = language == "zh_my";
            let meridian = c.get(4).map(|g| {
                let a = g.as_str().replace(".", "").to_lowercase();
                if a == "am" {
                    if zh_my_variant { "早上".to_string() } else { "上午".to_string() }
                } else if a == "pm" {
                    if h <= 6 { "下午".to_string() } else { "晚上".to_string() }
                } else { a }
            });
            let base = if m == 0 {
                format!("{}点", crate::normalize_zh::to_cardinal_zh(h as u128))
            } else {
                format!(
                    "{}点{}分",
                    crate::normalize_zh::to_cardinal_zh(h as u128),
                    crate::normalize_zh::to_cardinal_zh(m as u128)
                )
            };
            return match meridian {
                Some(w) => format!("{w}{base}"),
                None => base,
            };
        }
        return text.to_string();
    }
    let cardinal = |n: u128| cardinal_for(n, language);
    let re = fancy_regex::Regex::new(
        r"(?i)\b(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.|pagi|petang|siang|sore|malam|tengah\s+hari)?",
    )
    .unwrap();
    if let Ok(Some(caps)) = re.captures(text) {
        let hour = caps.get(1).map(|m| m.as_str()).unwrap_or("0");
        let minute = caps.get(2).map(|m| m.as_str()).unwrap_or("0");
        let mut out = format!(
            "{} {}",
            cardinal(hour.parse().unwrap_or(0)),
            cardinal(minute.parse().unwrap_or(0))
        );
        if let Some(sec) = caps.get(3) {
            out.push_str(&format!(" {}", cardinal(sec.as_str().parse().unwrap_or(0))));
        }
        if let Some(mer) = caps.get(4) {
            let m = mer.as_str();
            let word = if m.eq_ignore_ascii_case("am") || m.eq_ignore_ascii_case("a.m.") {
                if language == "en" { "a m" } else { "pagi" }
            } else if m.eq_ignore_ascii_case("pm") || m.eq_ignore_ascii_case("p.m.") {
                match language {
                    "en" => "p m",
                    "id" => "sore",
                    _ => "petang",
                }
            } else if language == "en" {
                // python quirk preserved: ms/id meridian words in en text are
                // dropped (_convert_time_to_spoken maps only am/pm for en)
                ""
            } else {
                m.trim()
            };
            out.push_str(&format!(" {word}"));
        }
        return out;
    }
    text.to_string()
}
