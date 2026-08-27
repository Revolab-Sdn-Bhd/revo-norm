//! pybind — PyO3 surface exposing the pipeline to python. Built as the
//! `revonorm._core` extension module via maturin; the wasm/cdylib
//! targets are unaffected.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use crate::num2word::to_cardinal as ms_cardinal;

#[pyfunction]
#[pyo3(signature = (text, language, options_json=""))]
#[pyo3(name = "normalize")]
fn normalize_py(text: &str, language: &str, options_json: &str) -> PyResult<String> {
    let opts = crate::options::Options::parse(options_json)
        .map_err(PyValueError::new_err)?;
    crate::pipeline::normalize_with(text, language, &opts)
        .map_err(PyValueError::new_err)
}

#[pyfunction]
#[pyo3(name = "supported_languages")]
fn supported_languages_py() -> Vec<String> {
    crate::langpack::supported_languages()
        .into_iter()
        .map(String::from)
        .collect()
}

// --- num2word surfaces (ms/id/zh) used by the parity test suite ----------

#[pyfunction]
#[pyo3(name = "to_cardinal_ms")]
fn to_cardinal_ms_py(n: u128) -> String {
    ms_cardinal(n)
}

/// Engine entity extraction: returns (protected_text, [(tag, text, id), ...])
/// with `<<<TAG_ID>>>` placeholders — all 13 types, python's extraction order.
/// Extract with an optional type filter: tags is a list of engine tags
/// (URL, EMAIL, ...); empty means extract everything. Returns
/// (protected_text, [(tag, text, id), ...]) with ids numbered in result
/// order (python semantics: next_id increments per claimed entity).
#[pyfunction]
#[pyo3(name = "extract_entities")]
#[pyo3(signature = (text, tags=None))]
fn extract_entities_py(
    text: &str,
    tags: Option<Vec<String>>,
) -> (String, Vec<(String, String, u32)>) {
    let (protected, entities) = crate::entities::extract(text);
    let filter: Option<std::collections::HashSet<String>> =
        tags.map(|t| t.into_iter().collect());
    let mut list = Vec::new();
    let mut next_id = 1u32;
    for e in &entities {
        if let Some(f) = &filter {
            if !f.contains(e.kind.tag()) {
                continue;
            }
        }
        list.push((e.kind.tag().to_string(), e.text.clone(), next_id));
        next_id += 1;
    }
    (protected, list)
}

/// Engine entity speech: convert one extracted entity to its spoken form.
#[pyfunction]
#[pyo3(name = "entity_to_spoken")]
fn entity_to_spoken_py(text: &str, tag: &str, language: &str) -> PyResult<String> {
    let kind = crate::entities::entity_kind_from_tag(tag);
    crate::entities::speak_entity(kind, text, language).map_err(PyValueError::new_err)
}

#[pyfunction]
#[pyo3(name = "to_cardinal_id")]
#[pyo3(signature = (n, /))]
fn to_cardinal_id_py(n: i64) -> PyResult<String> {
    if n < 0 {
        return Ok(format!("negatif {}", crate::num2word::to_cardinal_id((-n) as u128)));
    }
    Ok(crate::num2word::to_cardinal_id(n as u128))
}

#[pyfunction]
#[pyo3(name = "to_cardinal_zh")]
fn to_cardinal_zh_py(n: f64) -> PyResult<String> {
    if n.abs() >= 10_f64.powi(16) {
        return Err(pyo3::exceptions::PyOverflowError::new_err(format!(
            "Number {n} is too large (max 10^16)"
        )));
    }
    Ok(to_cardinal_zh_inner(n))
}

fn to_cardinal_zh_inner(n: f64) -> String {
    if n < 0.0 {
        return format!("负{}", crate::normalize_zh::to_cardinal_zh(n.abs() as u128));
    }
    if n.fract() != 0.0 {
        let int_part = n.trunc() as u128;
        let dec: String = {
            let s = format!("{n}");
            match s.split_once('.') {
                Some((_, d)) => d
                    .chars()
                    .map(|c| crate::normalize_zh::to_cardinal_zh((c as u8 - b'0') as u128))
                    .collect(),
                None => String::new(),
            }
        };
        return format!(
            "{}点{}",
            crate::normalize_zh::to_cardinal_zh(int_part),
            dec
        );
    }
    crate::normalize_zh::to_cardinal_zh(n as u128)
}

#[pyfunction]
#[pyo3(name = "to_currency_zh")]
fn to_currency_zh_py(value: f64, currency: &str) -> String {
    let int_part = value.trunc() as u128;
    let cents = ((value.fract()) * 100.0).round() as i64;
    // the spoken unit IS the currency string (python: to_cardinal(n) + currency)
    let unit = currency;
    if cents > 0 {
        format!(
            "{}{}{}分",
            crate::normalize_zh::to_cardinal_zh(int_part),
            unit,
            crate::normalize_zh::to_cardinal_zh(cents as u128)
        )
    } else {
        format!("{}{}", crate::normalize_zh::to_cardinal_zh(int_part), unit)
    }
}

#[pyfunction]
#[pyo3(name = "to_year_zh")]
fn to_year_zh_py(year: i64) -> String {
    crate::normalize_zh::to_year_zh(year.unsigned_abs() as u128)
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(normalize_py, m)?)?;
    m.add_function(wrap_pyfunction!(supported_languages_py, m)?)?;
    m.add_function(wrap_pyfunction!(to_cardinal_ms_py, m)?)?;
    m.add_function(wrap_pyfunction!(extract_entities_py, m)?)?;
    m.add_function(wrap_pyfunction!(entity_to_spoken_py, m)?)?;
    m.add_function(wrap_pyfunction!(to_cardinal_id_py, m)?)?;
    m.add_function(wrap_pyfunction!(to_cardinal_zh_py, m)?)?;
    m.add_function(wrap_pyfunction!(to_currency_zh_py, m)?)?;
    m.add_function(wrap_pyfunction!(to_year_zh_py, m)?)?;
    Ok(())
}
