//! options — the FFI/wasm config surface, mirroring the python Config fields
//! that affect normalization output.
//!
//! JSON shape (snake_case, matching python's Config attribute names):
//!   {"profile": "standard", "disable": ["acronyms"],
//!    "pronunciation_profile": "builtin",
//!    "pronunciations": {"*": {"WiFi": "wai fai"}, "ms": {"Dato": null}}}
//!
//! An empty/omitted field means the python default. Unknown fields are
//! rejected loudly (serde deny_unknown_fields) — a typo'd key must not
//! silently no-op.

use serde::Deserialize;

#[derive(Debug, Clone, Default, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Options {
    /// "minimal" | "basic" | "standard" | "aggressive"
    #[serde(default)]
    pub profile: Option<String>,
    /// Feature names to turn off (Config field names)
    #[serde(default)]
    pub disable: Vec<String>,
    /// Named pronunciation profile: "builtin" (default) | "none" | custom
    #[serde(default)]
    pub pronunciation_profile: Option<String>,
    /// Flat (all languages) or scoped ({"*": {...}, "ms": {...}}) overrides;
    /// null values delete the term from lower layers
    #[serde(default)]
    pub pronunciations: PronunciationScopes,
}

/// Language-scoped pronunciation table. A flat dict deserializes into
/// `star`; keyed scopes land in `scopes`.
#[derive(Debug, Clone, Default, Deserialize)]
pub struct PronunciationScopes {
    #[serde(default, rename = "*")]
    pub star: Option<std::collections::HashMap<String, Option<String>>>,
    #[serde(default, flatten)]
    pub scopes: std::collections::HashMap<String, std::collections::HashMap<String, Option<String>>>,
}

impl Options {
    /// Parse from JSON; empty string means defaults.
    pub fn parse(json: &str) -> Result<Self, String> {
        if json.trim().is_empty() {
            return Ok(Self::default());
        }
        serde_json::from_str(json).map_err(|e| format!("invalid options JSON: {e}"))
    }

    pub fn is_enabled(&self, feature: &str) -> bool {
        self.active(feature).unwrap_or(true)
            && !self.disable.iter().any(|d| d == feature)
    }

    /// The effective feature set: profile defaults minus disable overrides.
    /// Mirrors python Config.from_profile + per-field False.
    pub fn active(&self, feature: &str) -> Option<bool> {
        const OFF_MINIMAL: &[&str] = &[
            "abbreviations", "acronyms", "dates", "elongated", "fractions",
            "hari_bulan", "hijri", "ic", "malay_local", "measurements",
            "pronunciation_overrides", "special_chars", "strip_bracketed",
            "temperature", "times", "x_kali",
        ];
        const OFF_BASIC: &[&str] = &[
            "dates", "fractions", "hari_bulan", "hijri", "ic", "measurements",
            "pronunciation_overrides", "strip_bracketed", "temperature",
            "times", "x_kali",
        ];
        let off: &[&str] = match self.profile.as_deref() {
            Some("minimal") => OFF_MINIMAL,
            Some("basic") => OFF_BASIC,
            // standard and aggressive: everything on
            _ => return Some(true),
        };
        Some(!off.contains(&feature))
    }

    pub fn pronunciation_profile(&self) -> &str {
        self.pronunciation_profile.as_deref().unwrap_or("builtin")
    }

    /// Merged flat table for a language: builtin < profile < user scopes;
    /// later layers win, None deletes.
    pub fn resolve_pronunciations(
        &self,
        language: &str,
    ) -> Vec<(String, String)> {
        let mut merged: std::collections::HashMap<String, String> = Default::default();
        if self.pronunciation_profile() != "none" {
            for (term, spoken) in crate::pron::builtin_for(language) {
                merged.insert(term.to_string(), spoken.to_string());
            }
        }
        let user = &self.pronunciations;
        let apply = |merged: &mut std::collections::HashMap<String, String>,
                     table: &std::collections::HashMap<String, Option<String>>| {
            for (term, val) in table {
                match val {
                    Some(spoken) => {
                        merged.insert(term.clone(), spoken.clone());
                    }
                    None => {
                        merged.remove(term);
                    }
                }
            }
        };
        if let Some(star) = &user.star {
            apply(&mut merged, star);
        }
        if let Some(scope) = user.scopes.get(language) {
            apply(&mut merged, scope);
        }
        let mut v: Vec<(String, String)> = merged.into_iter().collect();
        v.sort_by(|a, b| b.0.len().cmp(&a.0.len()).then(a.0.cmp(&b.0)));
        v
    }
}
