//! normalizer_ms — faithful Rust port of revo_norm/normalizer_ms.py.
//!
//! Same pass order as normalize_malay():
//!   K-suffix -> date(ymd) -> date -> currency -> time(no-meridian)
//!   -> time -> percentage -> decimal -> dashed-digits -> comma-numbers
//!   -> adjacent-join -> bare numbers -> mixed-alnum
//!
//! Every rule's output must match tests/normalize_fixtures.txt (generated
//! from the python implementation) exactly — including the quirks.

use crate::num2word::to_cardinal;
use fancy_regex::Regex;
use std::sync::LazyLock;

fn digit_word(ch: char) -> &'static str {
    match ch {
        '0' => "kosong",
        '1' => "satu",
        '2' => "dua",
        '3' => "tiga",
        '4' => "empat",
        '5' => "lima",
        '6' => "enam",
        '7' => "tujuh",
        '8' => "lapan",
        '9' => "sembilan",
        _ => "",
    }
}

fn digit_word_upper(ch: char) -> String {
    if ch.is_ascii_digit() {
        digit_word(ch).to_string()
    } else {
        ch.to_uppercase().to_string()
    }
}

static MONTHS: LazyLock<std::collections::HashMap<&'static str, &'static str>> =
    LazyLock::new(|| {
        [
            ("1", "Januari"),
            ("2", "Februari"),
            ("3", "Mac"),
            ("4", "April"),
            ("5", "Mei"),
            ("6", "Jun"),
            ("7", "Julai"),
            ("8", "Ogos"),
            ("9", "September"),
            ("10", "Oktober"),
            ("11", "November"),
            ("12", "Disember"),
        ]
        .into_iter()
        .collect()
    });

static RE_K_SUFFIX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<!\w)(RM|Rp|\$|£|€|USD|EUR|GBP|MYR|IDR)(?:\s?)(\d+(?:\.\d+)?)K\b").unwrap()
});
static RE_T_SUFFIX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<!\w)(RM|Rp|\$|£|€|USD|EUR|GBP|MYR|IDR)(?:\s?)(\d+(?:\.\d+)?)T\b").unwrap()
});
static RE_TRILIUN_SUFFIX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<!\w)(RM|Rp|\$|£|€|USD|EUR|GBP|MYR|IDR)(?:\s?)(\d+(?:\.\d+)?)\s+(?:trilion|triliun)\b").unwrap()
});
static RE_B_SUFFIX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<!\w)(RM|Rp|\$|£|€|USD|EUR|GBP|MYR|IDR)(?:\s?)(\d+(?:\.\d+)?)B\b").unwrap()
});
static RE_MILIAR_SUFFIX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<!\w)(RM|Rp|\$|£|€|USD|EUR|GBP|MYR|IDR)(?:\s?)(\d+(?:\.\d+)?)\s+miliar\b").unwrap()
});
static RE_M_SUFFIX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<!\w)(RM|Rp|\$|£|€|USD|EUR|GBP|MYR|IDR)(?:\s?)(\d+(?:\.\d+)?)M\b").unwrap()
});
static RE_JUTA_SUFFIX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<!\w)(RM|Rp|\$|£|€|USD|EUR|GBP|MYR|IDR)(?:\s?)(\d+(?:\.\d+)?)\s+juta\b").unwrap()
});
static RE_RIBU_SUFFIX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<!\w)(RM|Rp|\$|£|€|USD|EUR|GBP|MYR|IDR)(?:\s?)(\d+(?:\.\d+)?)\s+ribu\b").unwrap()
});
static RE_DATE_YMD: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})\b").unwrap());
static RE_DATE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b").unwrap());
static RE_CURRENCY: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<!\w)(RM|\$|£|€|USD|EUR|GBP|MYR)(?:\s?)([\d,]+(?:[\.,]\d{1,2})?)(?:\s+(juta|bilion|trilion|ribu|million|billion|trillion|thousand))?\b").unwrap()
});
static RE_TIME_HOUR_ONLY: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.|malam|petang|pagi|siang|tengah hari)\b").unwrap()
});
static RE_TIME_NO_MERIDIAN: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b(\d{1,2}):(\d{2})\b(?!\s*(?:am|pm|a\.m\.|p\.m\.|malam|petang))(?!.*%)").unwrap()
});
static RE_TIME: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b(\d{1,2})[:\.](\d{2})\s*(?:(am|pm|a\.m\.|p\.m\.|malam|petang))").unwrap()
});
static RE_PERCENT: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b(\d+(?:\.\d+)?)%").unwrap());
static RE_DECIMAL: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\b(\d+)\.(\d+)\b").unwrap());
static RE_DASHED: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<![A-Za-z])([+\d]+(?:-[\d]+)+)(?![A-Za-z])").unwrap());
static RE_COMMA_NUM: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b\d{1,3}(?:,\d{3})+\b").unwrap());
static RE_ADJACENT: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<!\S)(\d+(?:\s+\d+)+)(?=[\s.,!?]|$)").unwrap());
static RE_NUMBER: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\b\d+\b").unwrap());
static RE_ALNUM: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\b[\w-]+\b").unwrap());

fn parse_num(s: &str) -> u128 {
    s.replace(',', "").parse().unwrap_or(0)
}


fn expand_k_suffix(text: &str) -> String {
    expand_suffix(text, &RE_K_SUFFIX, 1_000.0)
}

/// Expand `<symbol><amount><suffix-word>` to `<symbol><amount * mult>`,
/// matching python currency_utils.expand_currency_*_suffix (int when whole).
fn expand_suffix(text: &str, re: &Regex, mult: f64) -> String {
    re.replace_all(text, |c: &fancy_regex::Captures<str>| {
        let symbol = &c[1];
        let amount: f64 = c[2].parse().unwrap_or(0.0);
        let v = amount * mult;
        let s = if v.fract() == 0.0 {
            format!("{}", v as i64)
        } else {
            format!("{v}")
        };
        format!("{symbol}{s}")
    })
    .into_owned()
}

/// All currency-suffix expansions, in python pipeline order:
/// T/triliun -> B/miliar -> M/juta -> K/ribu.
pub fn expand_all_currency_suffixes(text: &str) -> String {
    let t = expand_suffix(text, &RE_T_SUFFIX, 1e12);
    let t = expand_suffix(&t, &RE_TRILIUN_SUFFIX, 1e12);
    let t = expand_suffix(&t, &RE_B_SUFFIX, 1e9);
    let t = expand_suffix(&t, &RE_MILIAR_SUFFIX, 1e9);
    let t = expand_suffix(&t, &RE_M_SUFFIX, 1e6);
    let t = expand_suffix(&t, &RE_JUTA_SUFFIX, 1e6);
    let t = expand_suffix(&t, &RE_K_SUFFIX, 1e3);
    expand_suffix(&t, &RE_RIBU_SUFFIX, 1e3)
}

/// Same, minus the en-semantics M (=million) pass — python skips it for id
/// where preparse already rewrites Rp-slang M to "miliar".
pub fn expand_suffixes_no_m(text: &str) -> String {
    let t = expand_suffix(text, &RE_T_SUFFIX, 1e12);
    let t = expand_suffix(&t, &RE_TRILIUN_SUFFIX, 1e12);
    let t = expand_suffix(&t, &RE_B_SUFFIX, 1e9);
    let t = expand_suffix(&t, &RE_MILIAR_SUFFIX, 1e9);
    let t = expand_suffix(&t, &RE_JUTA_SUFFIX, 1e6);
    let t = expand_suffix(&t, &RE_K_SUFFIX, 1e3);
    expand_suffix(&t, &RE_RIBU_SUFFIX, 1e3)
}

fn normalize_dates(text: &str) -> String {
    let t = RE_DATE_YMD.replace_all(text, |c: &fancy_regex::Captures<str>| {
        let month = MONTHS.get(c[2].trim_start_matches('0')).copied().unwrap_or(&c[2]);
        format!("{} {month} {}", to_cardinal(parse_num(&c[3])), to_cardinal(parse_num(&c[1])))
    });
    RE_DATE.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let month = MONTHS.get(c[2].trim_start_matches('0')).copied().unwrap_or(&c[2]);
        format!("{} {month} {}", to_cardinal(parse_num(&c[1])), to_cardinal(parse_num(&c[3])))
    })
    .into_owned()
}

fn normalize_currency(text: &str) -> String {
    RE_CURRENCY
        .replace_all(text, |c: &fancy_regex::Captures<str>| {
            let symbol = c[1].to_uppercase();
            let amount = c[2].replace(',', "");
            let magnitude = c
                .get(3)
                .map(|m| {
                    let w = m.as_str().to_lowercase();
                    match w.as_str() {
                        "million" => "juta".to_string(),
                        "billion" => "bilion".to_string(),
                        "trillion" => "trilion".to_string(),
                        "thousand" => "ribu".to_string(),
                        other => other.to_string(),
                    }
                })
                .filter(|m| !m.is_empty());
            let (unit_main, unit_sub) = match symbol.as_str() {
                "RM" | "MYR" => ("ringgit", "sen"),
                "$" | "USD" => ("dollar", "sen"),
                "£" | "GBP" => ("pound", "pence"),
                "€" | "EUR" => ("euro", "sen"),
                _ => ("unit", "subunit"),
            };
            if let Some(mag) = magnitude {
                if let Some((whole, frac)) = amount.split_once('.') {
                    let frac_words =
                        frac.chars().map(|d| to_cardinal(d.to_digit(10).unwrap() as u128))
                            .collect::<Vec<_>>().join(" ");
                    return format!("{} perpuluhan {} {mag} {unit_main}",
                                   to_cardinal(parse_num(whole)), frac_words);
                }
                return format!("{} {mag} {unit_main}", to_cardinal(parse_num(&amount)));
            }
            if let Some((ringgit, sen)) = amount.split_once('.') {
                if sen != "00" {
                    return format!("{} {unit_main} {} {unit_sub}",
                        to_cardinal(parse_num(ringgit)),
                        to_cardinal(parse_num(sen.get(..2).unwrap_or(sen))));
                }
                return format!("{} {unit_main}", to_cardinal(parse_num(ringgit)));
            }
            format!("{} {unit_main}", to_cardinal(parse_num(&amount)))
        })
        .into_owned()
}

fn normalize_times(text: &str) -> String {
    let t = RE_TIME_NO_MERIDIAN.replace_all(text, |c: &fancy_regex::Captures<str>| {
        let (h, m): (u32, u32) = (c[1].parse().unwrap_or(0), c[2].parse().unwrap_or(0));
        if h == 0 && m == 0 {
            return "tengah malam".to_string();
        }
        if h == 12 && m == 0 {
            return "tengah hari".to_string();
        }
        let minute = to_cardinal(m as u128);
        if minute == "kosong" {
            to_cardinal(h as u128)
        } else {
            format!("{} {}", to_cardinal(h as u128), minute)
        }
    });
    RE_TIME.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let meridian = c[3].to_lowercase();
        let meridian_word = if meridian.chars().count() > 2 {
            c[3].to_string()
        } else {
            format!("{} m", meridian.chars().next().unwrap_or('a'))
        };
        let minute = to_cardinal(c[2].parse::<u128>().unwrap_or(0));
        let hour = to_cardinal(c[1].parse::<u128>().unwrap_or(0));
        if minute == "kosong" {
            format!("{hour} {meridian_word}").trim().to_string()
        } else {
            format!("{hour} {minute} {meridian_word}").trim().to_string()
        }
    })
    .into_owned()
}

fn normalize_percent_decimal(text: &str) -> String {
    let t = RE_PERCENT.replace_all(text, |c: &fancy_regex::Captures<str>| {
        let n = &c[1];
        if let Some((whole, frac)) = n.split_once('.') {
            let frac_words = frac.chars()
                .map(|d| to_cardinal(d.to_digit(10).unwrap() as u128))
                .collect::<Vec<_>>().join(" ");
            format!("{} perpuluhan {frac_words} peratus", to_cardinal(parse_num(whole)))
        } else {
            format!("{} peratus", to_cardinal(parse_num(n)))
        }
    });
    RE_DECIMAL.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let frac_words = c[2].chars()
            .map(|d| to_cardinal(d.to_digit(10).unwrap() as u128))
            .collect::<Vec<_>>().join(" ");
        format!("{} perpuluhan {frac_words}", to_cardinal(parse_num(&c[1])))
    })
    .into_owned()
}

/// mixed-alnum tokens: v2.3.1, INV1234, Beta 2.0 -> spelled pieces.
/// Faithful to normalize_mixed_alnum incl. its "perpuluhan" joiner and
/// uppercase pass-through for letters.
fn normalize_mixed_alnum(token: &str) -> String {
    let only_digits_dashes = token
        .replace('-', "")
        .chars()
        .all(|c| c.is_ascii_digit() || c == '+' || c == '-');
    if only_digits_dashes {
        return token.to_string();
    }
    let has_alpha = token.chars().any(|c| c.is_alphabetic());
    let has_digit = token.chars().any(|c| c.is_ascii_digit());
    if !(has_alpha && has_digit) {
        return token.to_string();
    }
    if token.contains('.') && !token.starts_with(|c: char| c.is_ascii_alphabetic()) {
        return token
            .chars()
            .filter(|c| c.is_alphanumeric())
            .map(digit_word_upper)
            .collect::<Vec<_>>()
            .join(" ");
    }
    if token.contains('.') {
        let parts: Vec<&str> = token.split('.').collect();
        let mut out: Vec<String> = Vec::new();
        for (i, part) in parts.iter().enumerate() {
            if part.chars().all(|c| c.is_alphabetic()) && !part.is_empty() {
                out.push(part.to_uppercase());
            } else if !part.is_empty() && part.chars().all(|c| c.is_ascii_digit()) {
                out.push(to_cardinal(parse_num(part)));
            } else if !part.is_empty() {
                out.push(part.chars().filter(|c| c.is_alphanumeric())
                    .map(digit_word_upper).collect::<Vec<_>>().join(" "));
            }
            if i < parts.len() - 1 {
                out.push("perpuluhan".to_string());
            }
        }
        return out.join(" ");
    }
    token
        .chars()
        .filter(|c| c.is_alphanumeric())
        .map(digit_word_upper)
        .collect::<Vec<_>>()
        .join(" ")
}

/// Full pipeline, same order as python normalize_malay.
pub fn normalize_malay(text: &str) -> String {
    let t = expand_k_suffix(text);
    let t = normalize_dates(&t);
    let t = normalize_currency(&t);
    let t = normalize_times(&t);

    // hour-only meridian times (jumpa 3 petang / jam 3 pm) — python's
    // _time_hour_only_re pass; must run after the HH:MM forms
    let t = RE_TIME_HOUR_ONLY.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let hour: u32 = c[1].parse().unwrap_or(0);
        let m = c[2].to_lowercase().replace('.', "");
        let word = match m.as_str() {
            "am" => "pagi",
            "pm" => if hour < 18 { "petang" } else { "malam" },
            other => other,
        };
        format!("{} {word}", to_cardinal(hour as u128))
    });

    let t = normalize_percent_decimal(&t);

    // dashed digit groups -> space-separated digits (03-8888 -> "0 3 8 8 8 8").
    // Python emits digits-with-spaces here, NOT words: the adjacent-join pass
    // below must still see one digit run ("0 3 8 8 8 8 8000" -> "0388888000")
    // so the whole phone number goes digit-by-digit. Word-joining happens in
    // the bare-number pass.
    let t = RE_DASHED.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        c[1].chars().filter(|ch| ch.is_ascii_digit()).map(|d| d.to_string()).collect::<Vec<_>>().join(" ")
    });

    // comma numbers
    let t = RE_COMMA_NUM.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        to_cardinal(parse_num(c.get(0).map(|m| m.as_str()).unwrap_or("0")))
    });

    // join adjacent digit groups before bare-number pass
    let t = RE_ADJACENT.replace_all(&t, |c: &fancy_regex::Captures<str>| c[0].replace(' ', ""));

    // bare numbers: >4 digits -> digit-by-digit, else cardinal
    let t = RE_NUMBER.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let s = c.get(0).map(|m| m.as_str()).unwrap_or("0");
        if s.len() > 4 {
            s.chars().map(|d| to_cardinal(d.to_digit(10).unwrap() as u128))
                .collect::<Vec<_>>().join(" ")
        } else {
            to_cardinal(parse_num(s))
        }
    });

    // mixed alnum tokens
    RE_ALNUM.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        normalize_mixed_alnum(c.get(0).map(|m| m.as_str()).unwrap_or(""))
    })
    .into_owned()
}
