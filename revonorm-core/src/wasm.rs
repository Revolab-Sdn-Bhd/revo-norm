//! wasm-bindgen surface — the browser entry point for revolab-web.
//! Exposes normalize_malay(String) -> String for the JS wrapper to call
//! before phonemization.

use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub fn normalize_malay(text: &str) -> String {
    crate::normalize::normalize_malay(text)
}

#[wasm_bindgen]
pub fn to_cardinal(n: u32) -> String {
    crate::num2word::to_cardinal(n as u128)
}
