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

#[pyfunction]
#[pyo3(name = "to_cardinal_id")]
fn to_cardinal_id_py(n: u128) -> String {
    crate::num2word::to_cardinal_id(n)
}

#[pyfunction]
#[pyo3(name = "to_cardinal_zh")]
fn to_cardinal_zh_py(n: f64) -> String {
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
    let unit = match currency {
        "ringgit" => "令吉",
        _ => "元",
    };
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
    m.add_function(wrap_pyfunction!(to_cardinal_id_py, m)?)?;
    m.add_function(wrap_pyfunction!(to_cardinal_zh_py, m)?)?;
    m.add_function(wrap_pyfunction!(to_currency_zh_py, m)?)?;
    m.add_function(wrap_pyfunction!(to_year_zh_py, m)?)?;
    Ok(())
}
