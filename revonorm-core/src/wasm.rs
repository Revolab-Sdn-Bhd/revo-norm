//! wasm-bindgen surface — the browser entry point for revolab-web.
//!
//! `normalize(text, language)` mirrors the Python API shape; errors come
//! back as prefixed strings because wasm-bindgen cannot panic across the
//! boundary.

use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub fn normalize(text: &str, language: &str) -> String {
    match crate::pipeline::normalize(text, language) {
        Ok(out) => out,
        Err(e) => format!("__ERROR__{e}"),
    }
}

/// `normalize` with an options JSON (profile / disable / pronunciations).
/// Invalid JSON returns an `__ERROR__`-prefixed string.
#[wasm_bindgen]
pub fn normalize_with_options(text: &str, language: &str, options_json: &str) -> String {
    let opts = match crate::options::Options::parse(options_json) {
        Ok(o) => o,
        Err(e) => return format!("__ERROR__{e}"),
    };
    match crate::pipeline::normalize_with(text, language, &opts) {
        Ok(out) => out,
        Err(e) => format!("__ERROR__{e}"),
    }
}

#[wasm_bindgen]
pub fn normalize_malay(text: &str) -> String {
    crate::normalize::normalize_malay(text)
}

#[wasm_bindgen]
pub fn to_cardinal(n: u32) -> String {
    crate::num2word::to_cardinal(n as u128)
}

#[wasm_bindgen]
pub fn supported_languages() -> String {
    crate::langpack::supported_languages().join(",")
}
