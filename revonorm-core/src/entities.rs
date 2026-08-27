//! entities — port of revo_norm/entity_extractor.py's extract→placeholder→
//! restore skeleton (milestone 2). Entity types whose spoken conversion is a
//! shared feature (fractions, hijri, hari-bulan, temperature, x-kali, IC)
//! land with milestone 3; the patterns here are Python's, verbatim.

use fancy_regex::Regex;
use std::sync::LazyLock;

use crate::langpack::get_pack;
use crate::num2word::to_cardinal;

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
            EntityType::Fraction => "FRACTION",
            EntityType::XKali => "X_KALI",
            EntityType::Ic => "IC",
            EntityType::HariBulan => "HARI_BULAN",
            EntityType::Hijri => "HIJRI",
        }
    }
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
static RE_TIME: LazyLock<Regex> = LazyLock::new(|| {
    let patterns = [
        r"\b\d{1,2}:\d{2}\s*(?:pagi|petang|siang|sore|malam|tengah\s+hari)\b",
        r"\b\d{1,2}:\d{2}\s*(?:am|pm|a\.m\.|p\.m\.)?(?![A-Za-z0-9_])",
        r"\b\d{1,2}:\d{2}:\d{2}\b",
    ];
    Regex::new(&format!("(?i){}", patterns.iter().map(|p| format!("(?:{p})")).collect::<Vec<_>>().join("|"))).unwrap()
});

/// Python's extraction order (most specific first).
const ORDER: [EntityType; 13] = [
    EntityType::Url,
    EntityType::Email,
    EntityType::Phone,
    EntityType::Version,
    EntityType::Currency,
    EntityType::Date,
    EntityType::Time,
    EntityType::Temperature,
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
        other => return crate::shared::shared_pattern(other.tag()),
    };
    Some(re)
}

/// Extract entities and replace with `<<<TYPE_N>>>` placeholders.
pub fn extract(text: &str) -> (String, Vec<Entity>) {
    let mut entities = Vec::new();
    let mut protected = text.to_string();
    let mut next_id = 1usize;
    for kind in ORDER {
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
    let mut result = text.to_string();
    for e in entities.iter().rev() {
        let ph = format!("<<<{}_{}>>>", e.kind.tag(), e.placeholder_id);
        if let Some(pos) = result.find(&ph) {
            let spoken = convert_to_spoken(e, language);
            result.replace_range(pos..pos + ph.len(), &spoken);
        }
    }
    result
}

fn convert_to_spoken(e: &Entity, language: &str) -> String {
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
        EntityType::Currency => spoken_currency(&e.text),
        EntityType::Time => spoken_time(&e.text),
        EntityType::Url => spoken_url(&e.text, language),
        EntityType::Email => spoken_email(&e.text, language),
        EntityType::Version => spoken_version(&e.text),
        EntityType::Date => spoken_date(&e.text),
        // unreachable: shared_spoken handled these above
        EntityType::Temperature
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
    let mut spoken = url.to_string();
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
fn spoken_version(version: &str) -> String {
    version
        .split('.')
        .map(|p| to_cardinal(p.parse::<u128>().unwrap_or(0)))
        .collect::<Vec<_>>()
        .join(" point ")
}

/// python _convert_date_to_spoken (ms branch): day month-name year, each as
/// cardinal words.
fn spoken_date(date: &str) -> String {
    // slash format DD/MM/YYYY
    let re = fancy_regex::Regex::new(r"(?<![A-Za-z0-9_])(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})(?![A-Za-z0-9_])").unwrap();
    if let Ok(Some(c)) = re.captures(date) {
        let day = to_cardinal(c.get(1).map(|m| m.as_str()).unwrap_or("0").parse().unwrap_or(0));
        let month_num = c.get(2).map(|m| m.as_str()).unwrap_or("1");
        let year = to_cardinal(c.get(3).map(|m| m.as_str()).unwrap_or("0").parse().unwrap_or(0));
        let month = get_pack("ms")
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
fn spoken_currency(text: &str) -> String {
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
    let (unit_main, unit_sub) = match symbol.as_str() {
        "RM" | "MYR" => ("ringgit", "sen"),
        "RP" | "IDR" => ("rupiah", "sen"),
        "USD" | "$" => ("dollar", "cents"),
        "EUR" | "€" => ("euro", "cents"),
        "GBP" | "£" => ("pound", "pence"),
        _ => (&symbol[..], "cents"),
    };
    if let Some((whole, frac_raw)) = amount.split_once('.') {
        let mut frac = frac_raw.to_string();
        if frac.len() == 1 {
            frac.push('0');
        }
        let frac = &frac[..frac.len().min(2)];
        if !frac.is_empty() {
            let frac_spoken = to_cardinal(frac.parse::<u128>().unwrap_or(0));
            if whole == "0" {
                return format!("{frac_spoken} {unit_sub}");
            }
            return format!(
                "{} {unit_main} {frac_spoken} {unit_sub}",
                to_cardinal(whole.parse::<u128>().unwrap_or(0))
            );
        }
    }
    format!("{} {unit_main}", to_cardinal(amount.parse::<u128>().unwrap_or(0)))
}

fn spoken_time(text: &str) -> String {
    // python _convert_time_to_spoken (ms branch): hour minute [second] words
    // + meridian; minute always spoken ('sembilan kosong pagi').
    let re = fancy_regex::Regex::new(
        r"(?i)\b(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.|pagi|petang|siang|sore|malam|tengah\s+hari)?",
    )
    .unwrap();
    if let Ok(Some(caps)) = re.captures(text) {
        let hour = caps.get(1).map(|m| m.as_str()).unwrap_or("0");
        let minute = caps.get(2).map(|m| m.as_str()).unwrap_or("0");
        let mut out = format!(
            "{} {}",
            to_cardinal(hour.parse().unwrap_or(0)),
            to_cardinal(minute.parse().unwrap_or(0))
        );
        if let Some(sec) = caps.get(3) {
            out.push_str(&format!(" {}", to_cardinal(sec.as_str().parse().unwrap_or(0))));
        }
        if let Some(mer) = caps.get(4) {
            let m = mer.as_str();
            let word = if m.eq_ignore_ascii_case("am") || m.eq_ignore_ascii_case("a.m.") {
                "pagi"
            } else if m.eq_ignore_ascii_case("pm") || m.eq_ignore_ascii_case("p.m.") {
                "petang"
            } else {
                m.trim()
            };
            out.push_str(&format!(" {word}"));
        }
        return out;
    }
    text.to_string()
}
