//! normalize_id — Indonesian path, port of revo_norm/normalizer_id.py.
//! Self-contained like its python counterpart: same pass skeleton as ms
//! with id vocabulary, plus preparse (dotted thousands, comma decimals,
//! Rp slang suffixes where M = miliar).

use fancy_regex::Regex;
use std::sync::LazyLock;

use crate::num2word::to_cardinal_id;

static RE_DOTTED_THOUSANDS: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?<![\d.])(\d{1,3}(?:\.\d{3})+)(?:,(\d{1,2}))?(?!\.?\d)").unwrap()
});
static RE_COMMA_DECIMAL: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<![\d.,])(\d+),(\d{1,2})(?![\d.,])").unwrap());
static RE_ID_CURRENCY_SUFFIX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<!\w)((?:Rp|IDR)\s?\d+(?:\.\d+)?)\s*(rb|jt|K|M|B|T)\b").unwrap()
});
static RE_ID_BARE_SUFFIX: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?i)\b(\d+(?:\.\d+)?)\s*(rb|jt)\b").unwrap());

static RE_DATE_YMD: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})\b").unwrap());
static RE_DATE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b").unwrap());
static RE_PERCENT: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b(\d+(?:[.,]\d+)?)%").unwrap());
static RE_DECIMAL: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\b(\d+)\.(\d+)\b").unwrap());
static RE_DASHED: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<![A-Za-z])([+\d]+(?:-[\d]+)+)(?![A-Za-z])").unwrap());
static RE_COMMA_NUM: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b\d{1,3}(?:,\d{3})+\b").unwrap());
static RE_ADJACENT: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<!\S)(\d+(?:\s+\d+)+)(?=[\s.,!?]|$)").unwrap());
static RE_NUMBER: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\b\d+\b").unwrap());
static RE_ALNUM: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\b[\w-]+\b").unwrap());

static RE_TIME_HOUR_ONLY: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.|pagi|siang|sore|malam)\b").unwrap()
});
static RE_TIME_NO_MERIDIAN: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b(\d{1,2})[:\.](\d{2})\b(?!\s*(?:pagi|siang|sore|malam|am|pm|a\.m\.|p\.m\.))(?!.*%)").unwrap()
});
static RE_TIME: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b(\d{1,2})[:\.](\d{2})\s*(?:(pagi|siang|sore|malam|am|pm|a\.m\.|p\.m\.))").unwrap()
});

fn suffix_word(s: &str) -> &'static str {
    match s.to_lowercase().as_str() {
        "rb" | "k" => "ribu",
        "jt" => "juta",
        "m" | "b" => "miliar",
        "t" => "triliun",
        _ => "",
    }
}

fn parse_num(s: &str) -> u128 {
    s.replace(',', "").parse().unwrap_or(0)
}

/// Rewrite Indonesian written number conventions into the plain digit forms
/// the shared pipeline expects. Idempotent.
pub fn preparse_number_formats(text: &str) -> String {
    let dotted = RE_DOTTED_THOUSANDS
        .replace_all(text, |c: &fancy_regex::Captures<str>| {
            // decimal tail -> plain digits + dot decimal; integers keep
            // comma grouping (formatted cardinals downstream)
            let grouped = c[1].replace('.', "");
            match c.get(2) {
                Some(dec) => format!("{grouped}.{}", dec.as_str()),
                None => c[1].replace('.', ","),
            }
        })
        .into_owned();
    let comma = RE_COMMA_DECIMAL
        .replace_all(&dotted, |c: &fancy_regex::Captures<str>| {
            format!("{}.{}", &c[1], &c[2])
        })
        .into_owned();
    let currency = RE_ID_CURRENCY_SUFFIX
        .replace_all(&comma, |c: &fancy_regex::Captures<str>| {
            format!("{} {}", &c[1], suffix_word(&c[2]))
        })
        .into_owned();
    RE_ID_BARE_SUFFIX
        .replace_all(&currency, |c: &fancy_regex::Captures<str>| {
            format!("{} {}", &c[1], suffix_word(&c[2]))
        })
        .into_owned()
}

fn digit_word(ch: char) -> &'static str {
    match ch {
        '0' => "nol",
        '1' => "satu",
        '2' => "dua",
        '3' => "tiga",
        '4' => "empat",
        '5' => "lima",
        '6' => "enam",
        '7' => "tujuh",
        '8' => "delapan",
        '9' => "sembilan",
        _ => "",
    }
}

static MONTHS: LazyLock<std::collections::HashMap<&'static str, &'static str>> =
    LazyLock::new(|| {
        [
            ("1", "Januari"), ("2", "Februari"), ("3", "Maret"),
            ("4", "April"), ("5", "Mei"), ("6", "Juni"),
            ("7", "Juli"), ("8", "Agustus"), ("9", "September"),
            ("10", "Oktober"), ("11", "November"), ("12", "Desember"),
        ]
        .into_iter()
        .collect()
    });

/// Indonesian normalization pass, same order as python normalize_indonesian.
pub fn normalize_indonesian(text: &str) -> String {
    let t = preparse_number_formats(text);
    // currency suffixes (post-preparse plain forms; M already miliar-worded,
    // so the en-semantics M expansion must NOT run — python skips it for id)
    let t = crate::normalize::expand_suffixes_no_m(&t);

    let t = RE_DATE_YMD.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let month = MONTHS.get(c[2].trim_start_matches('0')).copied().unwrap_or(&c[2]);
        format!(
            "{} {month} {}",
            to_cardinal_id(parse_num(&c[3])),
            to_cardinal_id(parse_num(&c[1]))
        )
    });
    let t = RE_DATE.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let month = MONTHS.get(c[2].trim_start_matches('0')).copied().unwrap_or(&c[2]);
        format!(
            "{} {month} {}",
            to_cardinal_id(parse_num(&c[1])),
            to_cardinal_id(parse_num(&c[3]))
        )
    });

    // currency (Rp-first alternation like python's two-branch pattern)
    let t = normalize_currency_id(&t);

    // times: hour-only, no-meridian, meridian — id meridian mapping
    let t = RE_TIME_HOUR_ONLY.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let hour: u32 = c[1].parse().unwrap_or(0);
        let m = c[2].to_lowercase().replace('.', "");
        let word = match m.as_str() {
            "am" => "pagi",
            "pm" => "sore",
            other => other,
        };
        let _ = hour;
        format!("{} {word}", to_cardinal_id(c[1].parse().unwrap_or(0)))
    });
    let t = RE_TIME_NO_MERIDIAN.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let h: u32 = c[1].parse().unwrap_or(0);
        let m: u32 = c[2].parse().unwrap_or(0);
        if h == 0 && m == 0 {
            return "tengah malam".to_string();
        }
        if h == 12 && m == 0 {
            return "tengah hari".to_string();
        }
        if m == 0 {
            to_cardinal_id(h as u128)
        } else {
            format!("{} {}", to_cardinal_id(h as u128), to_cardinal_id(m as u128))
        }
    });
    let t = RE_TIME.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let h: u32 = c[1].parse().unwrap_or(0);
        let m: u32 = c[2].parse().unwrap_or(0);
        let mer = c[3].to_lowercase().replace('.', "");
        let word = match mer.as_str() {
            "am" => "pagi",
            "pm" => {
                if h < 18 { "sore" } else { "malam" }
            }
            other => other,
        };
        if m == 0 {
            format!("{} {word}", to_cardinal_id(h as u128))
        } else {
            format!("{} {} {word}", to_cardinal_id(h as u128), to_cardinal_id(m as u128))
        }
    });

    let t = RE_PERCENT.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let num = c[1].replace(',', ".");
        if let Some((w, f)) = num.split_once('.') {
            let fw = f.chars().map(|d| to_cardinal_id(d.to_digit(10).unwrap_or(0) as u128)).collect::<Vec<_>>().join(" ");
            format!("{} koma {fw} persen", to_cardinal_id(parse_num(w)))
        } else {
            format!("{} persen", to_cardinal_id(parse_num(&num)))
        }
    });
    let t = RE_DECIMAL.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let fw = c[2].chars().map(|d| to_cardinal_id(d.to_digit(10).unwrap_or(0) as u128)).collect::<Vec<_>>().join(" ");
        format!("{} koma {fw}", to_cardinal_id(parse_num(&c[1])))
    });

    // dashed -> space-separated digits (keeps adjacent-join semantics)
    let t = RE_DASHED.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        c[1].chars().filter(|ch| ch.is_ascii_digit()).map(|d| d.to_string()).collect::<Vec<_>>().join(" ")
    });
    let t = RE_COMMA_NUM.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        to_cardinal_id(parse_num(c.get(0).map(|m| m.as_str()).unwrap_or("0")))
    });
    let t = RE_ADJACENT.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        c[0].replace(' ', "")
    });
    let t = RE_NUMBER.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let s = c.get(0).map(|m| m.as_str()).unwrap_or("0");
        if s.len() > 4 {
            s.chars().map(|d| to_cardinal_id(d.to_digit(10).unwrap_or(0) as u128)).collect::<Vec<_>>().join(" ")
        } else {
            to_cardinal_id(parse_num(s))
        }
    });
    RE_ALNUM.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        normalize_mixed_alnum_id(c.get(0).map(|m| m.as_str()).unwrap_or(""))
    })
    .into_owned()
}

fn normalize_mixed_alnum_id(token: &str) -> String {
    let has_alpha = token.chars().any(|c| c.is_alphabetic());
    let has_digit = token.chars().any(|c| c.is_ascii_digit());
    if !has_alpha || !has_digit {
        return token.to_string();
    }
    // starts with digits: speak each alnum char
    if token.chars().next().is_some_and(|c| c.is_ascii_digit()) {
        return token
            .chars()
            .filter(|c| c.is_alphanumeric())
            .map(|c| if c.is_ascii_digit() { digit_word(c).to_string() } else { c.to_uppercase().to_string() })
            .collect::<Vec<_>>()
            .join(" ");
    }
    // starts with letters: split on '.' with koma between parts
    let parts: Vec<&str> = token.split('.').collect();
    let mut out: Vec<String> = Vec::new();
    for (i, part) in parts.iter().enumerate() {
        if part.chars().all(|c| c.is_alphabetic()) {
            out.push(part.to_uppercase());
        } else if !part.is_empty() && part.chars().all(|c| c.is_ascii_digit()) {
            out.push(to_cardinal_id(part.parse().unwrap_or(0)));
        } else if !part.is_empty() {
            out.push(
                part.chars()
                    .filter(|c| c.is_alphanumeric())
                    .map(|c| if c.is_ascii_digit() { digit_word(c).to_string() } else { c.to_uppercase().to_string() })
                    .collect::<Vec<_>>()
                    .join(" "),
            );
        }
        if i < parts.len() - 1 {
            out.push("koma".to_string());
        }
    }
    out.join(" ")
}

fn normalize_currency_id(text: &str) -> String {
    // python two-branch: Rp first, foreign second — single combined regex
    // with Rp alternation first preserves precedence.
    let re = fancy_regex::Regex::new(
        r"(?i)(?<!\w)(Rp|IDR)(?:\s?)([\d,]+(?:[\.,]\d{1,2})?)(?:\s+(juta|miliar|triliun|ribu|million|billion|trillion|thousand))?\b|(?<!\w)(RM|MYR|USD|EUR|GBP|\$|£|€)(?:\s?)([\d,]+(?:[\.,]\d{1,2})?)(?:\s+(juta|miliar|triliun|ribu|million|billion|trillion|thousand))?\b",
    )
    .unwrap();
    re.replace_all(text, |c: &fancy_regex::Captures<str>| {
        let is_rp = c.get(1).is_some();
        let symbol = if is_rp {
            c[1].to_uppercase()
        } else {
            c[4].to_uppercase()
        };
        let amount_raw = if is_rp { &c[2] } else { &c[5] };
        let magnitude = if is_rp { c.get(3) } else { c.get(6) };
        let amount = amount_raw.replace(',', "");
        let (unit_main, _unit_sub) = match symbol.as_str() {
            "RP" | "IDR" => ("rupiah", "sen"),
            "RM" | "MYR" => ("ringgit", "sen"),
            "$" | "USD" => ("dolar", "sen"),
            "£" | "GBP" => ("pound", "pence"),
            "€" | "EUR" => ("euro", "sen"),
            _ => ("unit", "subunit"),
        };
        let mag = magnitude.map(|m| {
            match m.as_str().to_lowercase().as_str() {
                "million" => "juta".to_string(),
                "billion" => "miliar".to_string(),
                "trillion" => "triliun".to_string(),
                "thousand" => "ribu".to_string(),
                other => other.to_string(),
            }
        });
        if let Some(mag) = mag.filter(|m| !m.is_empty()) {
            if let Some((w, f)) = amount.split_once('.') {
                let fw = f.chars().map(|d| to_cardinal_id(d.to_digit(10).unwrap_or(0) as u128)).collect::<Vec<_>>().join(" ");
                return format!("{} koma {fw} {mag} {unit_main}", to_cardinal_id(parse_num(w)));
            }
            return format!("{} {mag} {unit_main}", to_cardinal_id(parse_num(&amount)));
        }
        if let Some((w, f)) = amount.split_once('.') {
            let fw = f.chars().map(|d| to_cardinal_id(d.to_digit(10).unwrap_or(0) as u128)).collect::<Vec<_>>().join(" ");
            return format!("{} {unit_main} {fw} sen", to_cardinal_id(parse_num(w)));
        }
        format!("{} {unit_main}", to_cardinal_id(parse_num(&amount)))
    })
    .into_owned()
}
