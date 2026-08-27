//! misc_passes — the small pipeline passes ported from
//! revo_norm/text_normalizer.py and shared_features.py: USSD codes,
//! digit-by-digit contexts, elongated words, repeated-word commas.

use fancy_regex::Regex;
use std::collections::HashSet;
use std::sync::LazyLock;

use crate::langpack::get_pack;

static RE_USSD: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\*(\d+)#").unwrap());

static RE_DIGIT_CTX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b(exit|gate|lot|platform|bus\s+no|flight|stand|bay|block|blok)\s+(\d+)\b").unwrap()
});
static RE_PRODUCT_CTX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b(Office|Windows|PlayStation|PS|Xbox|iPhone|iPad|Galaxy|Pixel|Model|MacBook|AirPods)\s+(\d{3,})\b").unwrap()
});

static RE_ELONGATED: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"(.)\1{2,}").unwrap());

/// python _expand_ussd_codes: *120# -> "star satu dua kosong hash".
pub fn expand_ussd(text: &str, language: &str) -> String {
    let pack = get_pack(language);
    RE_USSD
        .replace_all(text, |c: &fancy_regex::Captures<str>| {
            let digits = c[1]
                .chars()
                .map(|d| pack.speak_digit(d))
                .collect::<Vec<_>>()
                .join(" ");
            format!("star {digits} hash")
        })
        .into_owned()
}

/// python _expand_digit_by_digit_context: numbers after exit/gate/lot/...
/// and product model numbers (iPhone 15 Pro) speak digit-by-digit.
pub fn expand_digit_contexts(text: &str, language: &str) -> String {
    let pack = get_pack(language);
    let sub = |re: &Regex, t: String| -> String {
        re.replace_all(&t, |c: &fancy_regex::Captures<str>| {
            let digits = c[2]
                .chars()
                .map(|d| pack.speak_digit(d))
                .collect::<Vec<_>>()
                .join(" ");
            format!("{} {digits}", &c[1])
        })
        .into_owned()
    };
    let t = sub(&RE_DIGIT_CTX, text.to_string());
    sub(&RE_PRODUCT_CTX, t)
}

/// python shared_features.normalize_elongated_text: reduce 3+ repeated
/// chars to 2 ("betuiii" -> "betuii"); skips ALL-CAPS (acronyms) and words
/// containing digits; "ke-" ordinals untouched (regex never matches inside
/// since ke- words lack triples — python guards, we mirror the guard).
pub fn normalize_elongated(text: &str) -> String {
    let is_upper = |w: &str| w.chars().filter(|c| c.is_alphabetic()).all(|c| c.is_uppercase());
    text.split_whitespace()
        .map(|word| {
            if is_upper(word) || word.chars().any(|c| c.is_ascii_digit()) {
                word.to_string()
            } else if RE_ELONGATED.is_match(word).unwrap_or(false) {
                // python's word-level guard + char-class reduce
                RE_ELONGATED
                    .replace_all(word, |c: &fancy_regex::Captures<str>| {
                        let ch = c[1].chars().next().unwrap_or('x');
                        format!("{ch}{ch}")
                    })
                    .into_owned()
            } else {
                word.to_string()
            }
        })
        .collect::<Vec<_>>()
        .join(" ")
}

/// python tts_utils._DIGIT_WORDS — words that make repeated-word comma
/// insertion skip (digit sequences must not gain commas).
static DIGIT_WORDS: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    [
        "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "lapan", "sembilan", "kosong",
        "puluh", "ratus", "ribu", "juta", "belas", "perpuluhan",
        "delapan", "nol", "koma", "miliar", "triliun",
        "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "zero",
        "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
        "seventeen", "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty",
        "sixty", "seventy", "eighty", "ninety",
        "hundred", "thousand", "million", "billion", "point",
    ]
    .into_iter()
    .collect()
});

fn is_digit_word(word: &str) -> bool {
    let cleaned: String = word
        .trim_matches(|c: char| ",.;:!?".contains(c))
        .chars()
        .collect();
    let lower = cleaned.to_lowercase();
    DIGIT_WORDS.contains(lower.as_str())
}

/// python insert_comma_after_repeated_words: "test test test test" ->
/// "test test test, test"; skips when the word is a number-word so spoken
/// digit sequences never gain commas. Runs ALWAYS (no feature gate).
pub fn insert_comma_repeated(text: &str, min_repeat: usize) -> String {
    // fancy-regex supports backreferences
    let re = match Regex::new(&format!(r"\b(?P<word>\w+)\b(?: \k<word>){{{},{}}}", min_repeat, "")) {
        Ok(r) => r,
        Err(_) => return text.to_string(),
    };
    re.replace_all(text, |c: &fancy_regex::Captures<str>| {
        let word = c.name("word").map(|m| m.as_str()).unwrap_or("");
        if is_digit_word(word) {
            return c[0].to_string();
        }
        let words: Vec<&str> = c[0].split(' ').collect();
        let head = words[..words.len() - 1].join(" ");
        format!("{head}, {}", words[words.len() - 1])
    })
    .into_owned()
}
