//! normalize_en — English path, port of revo_norm/normalizer_en.py.
//! The number engine is num2word_en (inflect-formatting compatible).

use fancy_regex::Regex;
use std::collections::HashSet;
use std::sync::LazyLock;

use crate::num2word_en::{ordinal_word, to_cardinal_en};

const CONTRACTIONS: &[(&str, &str)] = &[
    ("I'm", "I am"), ("I've", "I have"), ("I'll", "I will"), ("I'd", "I would"),
    ("you're", "you are"), ("you've", "you have"), ("you'll", "you will"), ("you'd", "you would"),
    ("he's", "he is"), ("he'll", "he will"), ("he'd", "he would"),
    ("she's", "she is"), ("she'll", "she will"), ("she'd", "she would"),
    ("it's", "it is"), ("it'll", "it will"), ("it'd", "it would"),
    ("we're", "we are"), ("we've", "we have"), ("we'll", "we will"), ("we'd", "we would"),
    ("they're", "they are"), ("they've", "they have"), ("they'll", "they will"), ("they'd", "they would"),
    ("that's", "that is"), ("that'll", "that will"), ("that'd", "that would"),
    ("there's", "there is"), ("there'll", "there will"), ("there'd", "there would"),
    ("who's", "who is"), ("who'll", "who will"), ("who'd", "who would"),
    ("what's", "what is"), ("what'll", "what will"), ("what'd", "what would"),
    ("where's", "where is"), ("where'll", "where will"), ("where'd", "where would"),
    ("when's", "when is"), ("when'll", "when will"), ("when'd", "when would"),
    ("why's", "why is"), ("why'll", "why will"), ("why'd", "why would"),
    ("how's", "how is"), ("how'll", "how will"), ("how'd", "how would"),
    ("isn't", "is not"), ("aren't", "are not"), ("wasn't", "was not"), ("weren't", "were not"),
    ("hasn't", "has not"), ("haven't", "have not"), ("hadn't", "had not"),
    ("doesn't", "does not"), ("don't", "do not"), ("didn't", "did not"),
    ("won't", "will not"), ("wouldn't", "would not"), ("shan't", "shall not"),
    ("shouldn't", "should not"), ("can't", "cannot"), ("couldn't", "could not"),
    ("mustn't", "must not"),
    ("should've", "should have"), ("would've", "would have"), ("could've", "could have"),
    ("shall've", "shall have"), ("will've", "will have"), ("might've", "might have"),
    ("must've", "must have"),
];

const ABBREVIATIONS: &[(&str, &str)] = &[
    ("mrs", "misess"), ("mr", "mister"), ("dr", "doctor"), ("st", "saint"),
    ("co", "company"), ("jr", "junior"), ("maj", "major"), ("gen", "general"),
    ("drs", "doctors"), ("rev", "reverend"), ("lt", "lieutenant"), ("hon", "honorable"),
    ("sgt", "sergeant"), ("capt", "captain"), ("esq", "esquire"), ("ltd", "limited"),
    ("col", "colonel"), ("ft", "fort"),
];

static MONTHS: LazyLock<std::collections::HashMap<&'static str, &'static str>> =
    LazyLock::new(|| {
        [
            ("1", "January"), ("2", "February"), ("3", "March"), ("4", "April"),
            ("5", "May"), ("6", "June"), ("7", "July"), ("8", "August"),
            ("9", "September"), ("10", "October"), ("11", "November"), ("12", "December"),
        ]
        .into_iter()
        .collect()
    });

/// python IGNORE_WORDS: cardinals + ordinals 1..=31 (mixed-alnum guard).
static IGNORE_WORDS: LazyLock<HashSet<String>> = LazyLock::new(|| {
    let mut s = HashSet::new();
    for i in 1u64..=31 {
        s.insert(to_cardinal_en(i as u128));
        s.insert(ordinal_word(i));
    }
    s
});

fn digit_word(ch: char) -> &'static str {
    match ch {
        '0' => "zero", '1' => "one", '2' => "two", '3' => "three", '4' => "four",
        '5' => "five", '6' => "six", '7' => "seven", '8' => "eight", '9' => "nine",
        '+' => "plus",
        _ => "",
    }
}

static RE_DATE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b").unwrap());
static RE_CURRENCY: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<!\w)(RM|\$|£|€|USD|EUR|GBP|MYR)\s?([\d,]+(?:[\.,]\d{1,2})?)(?:\s+(million|billion|trillion|thousand))?\b").unwrap()
});
static RE_PERCENT: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b(\d+(?:\.\d+)?)%").unwrap());
static RE_DECIMAL: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\b(\d+)\.(\d+)\b").unwrap());
static RE_DASHED: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<![A-Za-z])([+\d]+(?:-[\d]+)+)(?![A-Za-z])").unwrap());
static RE_ORDINAL: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?i)\b(\d{1,2})(st|nd|rd|th)\b").unwrap());
static RE_COMMA_NUM: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\b\d{1,3}(?:,\d{3})+\b").unwrap());
static RE_NUMBER: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\b\d+\b").unwrap());
static RE_ALNUM: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\b[\w-]+\b").unwrap());
static RE_TIME_HOUR_ONLY: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?i)\b(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)\b").unwrap());
static RE_TIME_NO_MERIDIAN: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b(\d{1,2}):(\d{2})\b(?!\s*(?:am|pm|a\.m\.|p\.m\.))(?!.*%)").unwrap()
});
static RE_TIME: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b(\d{1,2})[:\.](\d{2})\s*(?:(am|pm|a\.m\.|p\.m\.))").unwrap()
});

fn parse_num(s: &str) -> u128 {
    s.replace(',', "").parse().unwrap_or(0)
}

fn cardinal(n: u128) -> String {
    to_cardinal_en(n)
}

/// Render a 4-digit number year-style (1990 -> "nineteen ninety").
pub fn render_year(num: u128) -> String {
    let first = num / 100;
    let second = num % 100;
    let first_word = cardinal(first);
    if second == 0 {
        if first == 20 { "two thousand".to_string() } else { format!("{first_word} hundred") }
    } else if second < 10 {
        format!("{first_word} oh {}", cardinal(second))
    } else {
        format!("{first_word} {}", cardinal(second))
    }
}

/// English normalization pass, same order as python text_normalize.
pub fn normalize_english(text: &str) -> String {
    let t = crate::normalize::expand_all_currency_suffixes(text);

    let t = RE_DATE.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let month = MONTHS.get(c[2].trim_start_matches('0')).copied().unwrap_or(&c[2]);
        format!(
            "{} of {month}, {}",
            ordinal_word(c[1].parse::<u64>().unwrap_or(0)),
            cardinal(parse_num(&c[3]))
        )
    });

    let t = RE_CURRENCY.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let symbol = c[1].to_uppercase();
        let amount = c[2].replace(',', "");
        let magnitude = c.get(3).map(|m| m.as_str().to_lowercase());
        let (unit_main, unit_sub) = match symbol.as_str() {
            "RM" | "MYR" => ("ringgit", "cent"),
            "$" | "USD" => ("dollar", "cent"),
            "£" => ("pound", "pence"),
            "€" => ("euro", "cent"),
            _ => ("unit", "subunit"),
        };
        if let Some(mag) = magnitude {
            if let Some((w, f)) = amount.split_once('.') {
                let fw = f.chars().map(|d| cardinal(d.to_digit(10).unwrap_or(0) as u128)).collect::<Vec<_>>().join(" ");
                return format!("{} point {fw} {mag} {unit_main}", cardinal(parse_num(w)));
            }
            return format!("{} {mag} {unit_main}", cardinal(parse_num(&amount)));
        }
        if let Some((major, minor_raw)) = amount.split_once('.') {
            let minor = &minor_raw[..minor_raw.len().min(2)];
            if minor != "00" && !minor.is_empty() {
                return format!("{} {unit_main} {} {unit_sub}", cardinal(parse_num(major)), cardinal(parse_num(minor)));
            }
            return format!("{} {unit_main}", cardinal(parse_num(major)));
        }
        format!("{} {unit_main}", cardinal(parse_num(&amount)))
    });

    let t = RE_TIME_HOUR_ONLY.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let m = c[2].to_lowercase().replace('.', "");
        let word = if m == "am" { "a m" } else { "p m" };
        format!("{} {word}", cardinal(c[1].parse().unwrap_or(0)))
    });
    let t = RE_TIME_NO_MERIDIAN.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let (h, m): (u128, u128) = (c[1].parse().unwrap_or(0), c[2].parse().unwrap_or(0));
        if h == 0 && m == 0 { return "midnight".to_string(); }
        if h == 12 && m == 0 { return "noon".to_string(); }
        if m == 0 { cardinal(h) } else { format!("{} {}", cardinal(h), cardinal(m)) }
    });
    let t = RE_TIME.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let (h, m): (u128, u128) = (c[1].parse().unwrap_or(0), c[2].parse().unwrap_or(0));
        let mer = c[3].to_lowercase();
        let chars: Vec<char> = mer.chars().collect();
        let word = format!("{} m", chars.first().copied().unwrap_or('a'));
        if m == 0 {
            format!("{} {word}", cardinal(h))
        } else {
            format!("{} {} {word}", cardinal(h), cardinal(m))
        }
    });

    let t = RE_PERCENT.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let num = &c[1];
        if let Some((w, f)) = num.split_once('.') {
            let fw = f.chars().map(|d| cardinal(d.to_digit(10).unwrap_or(0) as u128)).collect::<Vec<_>>().join(" ");
            format!("{} point {fw} percent", cardinal(parse_num(w)))
        } else {
            format!("{} percent", cardinal(parse_num(num)))
        }
    });
    let t = RE_DECIMAL.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let fw = c[2].chars().map(|d| cardinal(d.to_digit(10).unwrap_or(0) as u128)).collect::<Vec<_>>().join(" ");
        format!("{} point {fw}", cardinal(parse_num(&c[1])))
    });
    let t = RE_DASHED.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        c[1].chars().map(|ch| if ch == '-' { "dash".to_string() } else { digit_word(ch).to_string() }).collect::<Vec<_>>().join(" ")
    });
    let t = RE_ORDINAL.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        ordinal_word(c[1].parse::<u64>().unwrap_or(0))
    });
    let t = RE_COMMA_NUM.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        cardinal(parse_num(c.get(0).map(|m| m.as_str()).unwrap_or("0")))
    });
    let t = RE_NUMBER.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let s = c.get(0).map(|m| m.as_str()).unwrap_or("0");
        let num: u128 = s.parse().unwrap_or(0);
        if s.len() > 4 {
            s.chars().map(|d| cardinal(d.to_digit(10).unwrap_or(0) as u128)).collect::<Vec<_>>().join(" ")
        } else if s.len() == 4 && (1000..=2099).contains(&num) {
            render_year(num)
        } else {
            cardinal(num)
        }
    });
    let t = RE_ALNUM.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let token = c.get(0).map(|m| m.as_str()).unwrap_or("");
        mixed_alnum_en(token)
    });

    // contractions then abbreviations (whole-word, case-insensitive)
    let mut out = t.to_string();
    for (from, to) in CONTRACTIONS {
        if let Ok(re) = fancy_regex::Regex::new(&format!(r"(?i)\b{}\b", fancy_regex::escape(from))) {
            out = re.replace_all(&out, *to).into_owned();
        }
    }
    for (from, to) in ABBREVIATIONS {
        if let Ok(re) = fancy_regex::Regex::new(&format!(r"(?i)\b{}\.", fancy_regex::escape(from))) {
            out = re.replace_all(&out, *to).into_owned();
        }
    }
    // sdn bhd — optional dots
    if let Ok(re) = fancy_regex::Regex::new(r"(?i)\bsdn\.?\s+bhd\b\.?") {
        out = re.replace_all(&out, "sendirian berhad").into_owned();
    }
    squash(&out)
}

fn mixed_alnum_en(token: &str) -> String {
    let has_alpha = token.chars().any(|c| c.is_alphabetic());
    let has_digit = token.chars().any(|c| c.is_ascii_digit());
    if !has_alpha || !has_digit {
        return token.to_string();
    }
    if IGNORE_WORDS.contains(&token.to_lowercase()) {
        return token.to_string();
    }
    token
        .chars()
        .filter(|c| c.is_alphanumeric())
        .map(|c| if c.is_ascii_digit() { digit_word(c).to_string() } else { c.to_uppercase().to_string() })
        .collect::<Vec<_>>()
        .join(" ")
}

fn squash(text: &str) -> String {
    text.split_whitespace().collect::<Vec<_>>().join(" ")
}

// --- acronym + pronunciation-override passes (pipeline steps 6, shared
// across latin languages like python) ------------------------------------

/// python expand_acronym: preserve/split/spell tables + vowel heuristics.
pub fn expand_acronym(acronym: &str) -> String {
    const EXPAND_AS: &[(&str, &str)] = &[("SDN", "sendirian"), ("BHD", "berhad")];
    for (a, w) in EXPAND_AS {
        if acronym == *a {
            return (*w).to_string();
        }
    }
    const PRESERVE: &[&str] = &["NASA", "PLUS"];
    if PRESERVE.contains(&acronym) {
        return acronym.to_string();
    }
    const SPLIT: &[&str] = &["API", "GPU", "CPU", "AI", "ML", "DL", "NLP", "LLM", "RL", "PLUS"];
    if SPLIT.contains(&acronym) {
        return acronym.chars().map(|c| c.to_string()).collect::<Vec<_>>().join(" ");
    }
    const ALWAYS_SPELL: &[&str] = &["UITM", "UKM", "USM", "UTM", "UPNM", "IIUM", "UM", "UPM"];
    if ALWAYS_SPELL.contains(&acronym) {
        return acronym.chars().map(|c| c.to_string()).collect::<Vec<_>>().join(" ");
    }
    let vowels = ['a', 'e', 'i', 'o', 'u'];
    let is_vowel = |c: char| vowels.contains(&c.to_ascii_lowercase());
    let mut vowel_count = acronym.chars().filter(|c| is_vowel(*c)).count();
    if acronym.ends_with('y') || acronym.ends_with('Y') {
        vowel_count += 1;
    }
    let len = acronym.chars().count();
    let vowel_ratio = if len > 0 { vowel_count as f64 / len as f64 } else { 0.0 };
    let has_consonants = acronym
        .chars()
        .any(|c| !is_vowel(c) && !c.eq_ignore_ascii_case(&'y'));
    if len >= 4 && (0.3..=0.6).contains(&vowel_ratio) && has_consonants {
        return acronym.to_lowercase();
    }
    let rest: Vec<char> = acronym.chars().skip(1).collect::<Vec<_>>();
    // python rest[1:-1]: guard empty middles (single/double-char rests)
    let middle = if rest.len() > 2 { &rest[1..rest.len() - 1] } else { &[][..] };
    let has_vowel_in_middle = middle.iter().any(|c| is_vowel(*c));
    if rest.len() >= 3
        && !rest.first().is_some_and(|c| is_vowel(*c))
        && !rest.last().is_some_and(|c| is_vowel(*c))
        && has_vowel_in_middle
    {
        let joined: String = rest.iter().collect();
        return format!("{} {}", &acronym[..1], joined.to_lowercase());
    }
    acronym.chars().map(|c| c.to_string()).collect::<Vec<_>>().join(" ")
}

/// python replace_letter_period_sequences: I.B.M. -> I B M, letter-hyphen
/// -> space, then acronym expansion for 2-10 letter uppercase runs.
pub fn replace_letter_period_sequences(text: &str) -> String {
    let re_periods = fancy_regex::Regex::new(r"\b(?:[A-Za-z]\.){2,}\.?").unwrap();
    let t = re_periods
        .replace_all(text, |c: &fancy_regex::Captures<str>| {
            c[0].trim_end_matches('.').replace('.', " ")
        })
        .into_owned();
    let re_hyphen = fancy_regex::Regex::new(r"(?<=[A-Za-z])-(?=[A-Za-z])").unwrap();
    let t = re_hyphen.replace_all(&t, " ").into_owned();
    let re_acr = fancy_regex::Regex::new(r"\b[A-Z]{2,10}\b").unwrap();
    re_acr
        .replace_all(&t, |c: &fancy_regex::Captures<str>| expand_acronym(&c[0]))
        .into_owned()
}

/// python apply_pronunciation_overrides (latin branch).
pub fn apply_pronunciation_overrides(text: &str, language: &str) -> String {
    const OVERRIDES: &[(&str, &str)] = &[
        (r"(?i)\btwenty-three\b", "twenty tree"),
        (r"(?i)\bthree\b", "three"),
        (r"(?i)\btwenty-eight\b", "twenty, eight"),
        (r"(?i)\bcut-off\b", "kad off"),
        (r"(?i)\beighty-eight\b", "eighty eight"),
        (r"(?i)\bNumber\b", "number"),
        (r"(?i)\ba/l\b", "anak lelaki"),
        (r"(?i)\ba/p\b", "anak perempuan"),
        (r"(?i)\b1Malaysia\b", "satu malaysia"),
        (r"(?i)\bsdn\.?\s+bhd\b\.?", "sendirian berhad"),
    ];
    let mut out = text.to_string();
    for (pat, repl) in OVERRIDES {
        if let Ok(re) = fancy_regex::Regex::new(pat) {
            out = re.replace_all(&out, *repl).into_owned();
        }
    }
    // unit overrides (non-zh)
    // Unit overrides are latin-only: zh/zh_my skip them so measurements
    // ("10kg" -> 十公斤) see the raw form (python's not-in-zh gate).
    if !matches!(language, "zh" | "zh_my") {
        for (pat, spoken) in [
            (r"(?i)(\d+)\s*mg\b", "milligram"),
            (r"(?i)(\d+)\s*kg\b", "kilogram"),
            (r"(?i)(\d+)\s*GB\b", "gigabyte"),
        ] {
            if let Ok(re) = fancy_regex::Regex::new(pat) {
                out = re.replace_all(&out, format!("$1 {spoken}")).into_owned();
            }
        }
    }
    let no_word = match language {
        "ms" => "nombor",
        "id" => "nomor",
        _ => "number",
    };
    if let Ok(re) = fancy_regex::Regex::new(r"(?i)\bNo\.\s") {
        out = re.replace_all(&out, format!("{no_word} ")).into_owned();
    }
    out
}
