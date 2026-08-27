//! pron — port of revo_norm/pronunciation_mappings.py builtin profile +
//! whole-word application. Custom registered profiles (register_pronunciation_profile)
//! arrive via Options.pronunciations in the FFI surface; process-global
//! registration is a python-only legacy concept and is not ported.

use fancy_regex::Regex;


/// Builtin profile, language-scoped like python's BUILTIN_PROFILE.
/// Returns (term, spoken) pairs effective for `language`.
pub fn builtin_for(language: &str) -> Vec<(&'static str, &'static str)> {
    const ALL: &[(&str, &str)] = &[
        ("GUI", "gooey"),
        ("ASCII", "as key"),
        ("IEEE", "I triple E"),
        ("GIF", "gif"),
        ("WiFi", "wi fi"),
        ("iOS", "I O S"),
        ("UiTM", "U I T M"),
    ];
    const MS_ID: &[(&str, &str)] = &[
        ("Hj", "Haji"),
        ("Hjh", "Hajah"),
        ("Dr", "Doktor"),
        ("Prof", "Profesor"),
        ("Dato", "Dato"),
        ("Datin", "Datin"),
        ("Datuk", "Datuk"),
    ];
    match language {
        "ms" | "id" => {
            let mut v: Vec<(&str, &str)> = ALL.to_vec();
            v.extend_from_slice(MS_ID);
            v
        }
        _ => ALL.to_vec(),
    }
}

/// Apply a resolved (term, spoken) table: whole-word, case-insensitive,
/// longest-first — python apply_pronunciation_mappings.
pub fn apply(text: &str, table: &[(String, String)]) -> String {
    let mut result = text.to_string();
    for (term, spoken) in table {
        let Ok(re) = Regex::new(&format!(r"(?i)\b{}\b", fancy_regex::escape(term))) else {
            continue;
        };
        result = re.replace_all(&result, spoken.as_str()).into_owned();
    }
    result
}
