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

/// Normalize `text` for a language. `language` must be one of
/// `supported_languages()`; anything else returns an error message the
/// caller can surface (the Python library raises ValueError naming the code —
/// the wasm/C callers get the same message as an Err string).
pub fn normalize(text: &str, language: &str) -> Result<String, String> {
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

    // Language normalizer pass (currency, dates, times, numbers...).
    // Milestone 1 parity tier: python's full pipeline runs entity extraction
    // before this pass; cases where that changes output (dates/times/URLs)
    // are tracked in gen_fixtures.py ENTITY_CASES and asserted at the
    // normalizer tier until milestone 2 ports the extractor.
    out = normalize_malay(&out);

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
