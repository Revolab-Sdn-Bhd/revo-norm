//! langpack — Rust mirror of revo_norm/langpack.py.
//!
//! Every language is one `LanguagePack`: vocabulary tables plus the words
//! pipeline steps need (symbols, digits, months, negatives). Registered in
//! a global registry; adding a language means adding one module and one
//! `register` call — no edits to pipeline code.

use std::collections::HashMap;
use std::sync::LazyLock;

/// Vocabulary + behavior words for one language.
pub struct LanguagePack {
    pub code: &'static str,
    /// Symbol -> spoken form; empty string drops the symbol silently.
    pub symbol_words: HashMap<char, String>,
    /// Multi-char symbol -> spoken form (EUR, GBP).
    pub symbol_words_multi: HashMap<&'static str, String>,
    /// Single digit '0'-'9' -> spoken word.
    pub digit_words: HashMap<char, &'static str>,
    /// Spoken before a digit string when '-' means negative.
    pub negative_word: &'static str,
    /// Month number ("1".."12") -> month name.
    pub month_names: HashMap<&'static str, &'static str>,
    /// "!" is dropped silently (TTS over-emphasis).
    pub drops_exclamation: bool,
    /// Measurement unit -> spoken form (milestone 3).
    pub distance_units: HashMap<String, String>,
    pub volume_units: HashMap<String, String>,
    pub weight_units: HashMap<String, String>,
    pub duration_units: HashMap<String, String>,
    pub area_units: HashMap<String, String>,
    /// Temperature unit key ("c"/"f"/"k") -> spoken form.
    pub temperature_units: HashMap<String, String>,
    /// Fraction word ("per"), times word ("kali"), hijri suffix.
    pub fraction_word: &'static str,
    pub times_word: &'static str,
    pub hijri_suffix: &'static str,
}

/// The six measurement unit tables bundled for pack construction.
#[derive(Default)]
pub struct UnitTables {
    pub distance: HashMap<String, String>,
    pub volume: HashMap<String, String>,
    pub weight: HashMap<String, String>,
    pub duration: HashMap<String, String>,
    pub area: HashMap<String, String>,
    pub temperature: HashMap<String, String>,
}

impl LanguagePack {
    pub fn speak_digit(&self, ch: char) -> String {
        match self.digit_words.get(&ch) {
            Some(w) => (*w).to_string(),
            None => ch.to_string(),
        }
    }

}

static REGISTRY: LazyLock<HashMap<&'static str, &'static LanguagePack>> = LazyLock::new(|| {
    let mut m = HashMap::new();
    for pack in super::lang::all_packs() {
        m.insert(pack.code, pack);
    }
    m
});

/// Fetch the pack for a language code. Unknown codes panic here; the public
/// entry points validate first and return an error string instead.
pub fn get_pack(language: &str) -> &'static LanguagePack {
    REGISTRY
        .get(language.trim().to_lowercase().as_str())
        .unwrap_or_else(|| panic!("unsupported language: {language}"))
}

/// All registered language codes (sorted for stable display).
pub fn supported_languages() -> Vec<&'static str> {
    let mut v: Vec<&'static str> = REGISTRY.keys().copied().collect();
    v.sort_unstable();
    v
}

/// True when the code resolves to a registered pack.
pub fn is_supported(language: &str) -> bool {
    REGISTRY.contains_key(language.trim().to_lowercase().as_str())
}
