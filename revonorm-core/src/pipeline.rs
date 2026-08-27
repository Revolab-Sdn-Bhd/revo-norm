//! pipeline — mirrors revo_norm/text_normalizer.py's top-level flow for the
//! stages this crate implements (milestone 1): the language normalizer pass
//! wrapped by the pack-driven steps whose behavior is per-language data.
//!
//! Python order (subset): currency suffix -> ussd -> negative sign ->
//! [entity extraction: python-only for now] -> pronunciation mappings ->
//! [number normalization inside the language pass] -> special chars ->
//! exclamation drop.
//!
//! Differences from Python (documented, not ported yet): entity extraction,
//! pronunciation profile layers, URL/email speech. They land in later
//! milestones; parity fixtures only cover ported behavior.

use fancy_regex::Regex;
use std::sync::LazyLock;

use crate::langpack::{get_pack, is_supported};
use crate::normalize::normalize_malay;

static RE_NEG_SIGN: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<![\w\-])-(?=\d)").unwrap());
static RE_MULTI_SPACES: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\s+").unwrap());
static RE_EXCLAIM: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"!+").unwrap());
static RE_ENTITY_PH: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"<<<[A-Z_]+_(\d+)>>>").unwrap());

/// Replace entity placeholders with pure-alpha stash tokens (`entstashaa`,
/// `entstashab`, ...) that no language pass can match — port of python
/// _stash_placeholders. Returns (text, stash) where stash[i] holds the
/// original placeholder string for token i.
fn stash_placeholders(text: &str) -> (String, Vec<String>) {
    let mut stash: Vec<String> = Vec::new();
    let out = RE_ENTITY_PH
        .replace_all(text, |c: &fancy_regex::Captures<str>| {
            let idx = stash.len();
            stash.push(c.get(0).map(|m| m.as_str().to_string()).unwrap_or_default());
            format!("entstash{}", idx_to_letters(idx))
        })
        .into_owned();
    (out, stash)
}

/// 0→aa, 1→ab, ..., 25→az, 26→ba — python's _idx_to_letters.
fn idx_to_letters(mut n: usize) -> String {
    let letters = b"abcdefghijklmnopqrstuvwxyz";
    let mut out = Vec::new();
    loop {
        out.push(letters[n % 26] as char);
        n = if n >= 26 { (n / 26) - 1 } else { break };
    }
    out.reverse();
    out.into_iter().collect()
}

fn unstash_placeholders(text: &str, stash: &[String]) -> String {
    let mut out = text.to_string();
    for (i, ph) in stash.iter().enumerate() {
        out = out.replace(&format!("entstash{}", idx_to_letters(i)), ph);
    }
    out
}

/// Normalize `text` for a language. `language` must be one of
/// `supported_languages()`; anything else returns an error message the
/// caller can surface (the Python library raises ValueError naming the code —
/// the wasm/C callers get the same message as an Err string).
pub fn normalize(text: &str, language: &str) -> Result<String, String> {
    normalize_with(text, language, &crate::options::Options::default())
}

/// `normalize` with an options object (FFI callers parse from JSON).
pub fn normalize_with(
    text: &str,
    language: &str,
    options: &crate::options::Options,
) -> Result<String, String> {
    let code = language.trim().to_lowercase();
    if !is_supported(&code) {
        let langs = crate::langpack::supported_languages().join(", ");
        return Err(format!(
            "Unsupported language: '{language}' (expected one of ({langs}))"
        ));
    }
    if text.trim().is_empty() {
        return Ok(String::new());
    }

    // Milestone 1: only the Malay path has a ported normalizer. Others error
    // until their milestone lands — never silently fall back to Malay.
    if code != "ms" {
        return Err(format!(
            "language '{code}' not ported yet (milestone 1 ships 'ms'; en/id/zh/zh_my follow)"
        ));
    }

    let pack = get_pack(&code);
    let mut out = text.to_string();

    // Step 1 (python): currency suffix expansion — RM30K/RM1.5M/RM2 juta...
    // (inside normalize_malay too for the K case; idempotent at this level)
    out = crate::normalize::expand_all_currency_suffixes(&out);

    // Step 1c (python): negative signs — before number normalization.
    out = RE_NEG_SIGN
        .replace_all(&out, format!(" {} ", pack.negative_word))
        .into_owned();

    // Step 2.5 (python): measurements — before the language normalizer so
    // "5km" never becomes "lima K M" (acronym split).
    out = crate::shared::normalize_measurements(&out, &code);

    // Step 3 (python): entity extraction — claim entities with placeholders
    // so downstream passes cannot mangle them; restored after normalization.
    let (mut out, entities) = crate::entities::extract(&out);

    // Step 4 (python): pronunciation mappings on protected text.
    let pron_table = options.resolve_pronunciations(&code);
    out = crate::pron::apply(&out, &pron_table);

    // Step 5 (python): stash placeholders as pure-alpha tokens so language
    // normalizers (mixed-alnum, number passes) cannot touch them.
    let (out, stash) = stash_placeholders(&out);

    // Language normalizer pass (currency, dates, times, numbers...).
    let out = normalize_malay(&out);

    // Step 6.5: unstash back to <<<TYPE_N>>> placeholders.
    let mut out = unstash_placeholders(&out, &stash);

    // Step 7 (python): restore entities as spoken form.
    out = crate::entities::restore(&out, &entities, &code);

    // Special chars: spell out symbols from the pack table.
    for (ch, spoken) in &pack.symbol_words {
        out = out.replace(
            &ch.to_string(),
            &format!(" {spoken} "),
        );
    }
    for (sym, spoken) in &pack.symbol_words_multi {
        out = out.replace(sym, &format!(" {spoken} "));
    }

    // Exclamation drop where the pack opts in.
    if pack.drops_exclamation {
        out = RE_EXCLAIM.replace_all(&out, "").into_owned();
    }

    Ok(RE_MULTI_SPACES.replace_all(out.trim(), " ").into_owned())
}
