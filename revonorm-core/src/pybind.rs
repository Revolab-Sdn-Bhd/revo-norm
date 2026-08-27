//! pybind — PyO3 surface exposing the pipeline to python. Built as the
//! `revonorm_core._core` extension module via maturin; the wasm/cdylib
//! targets are unaffected.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

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

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(normalize_py, m)?)?;
    m.add_function(wrap_pyfunction!(supported_languages_py, m)?)?;
    Ok(())
}
