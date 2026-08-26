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
