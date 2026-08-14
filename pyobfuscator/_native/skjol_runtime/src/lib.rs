mod artifact;
mod cpython;
mod crypto;
mod metadata;
mod root_key;
mod runtime;

use pyo3::prelude::*;

#[pyfunction]
fn run(py: Python<'_>, name: &str, _file: &str, payload: &[u8]) -> PyResult<()> {
    runtime::run(py, name, payload)
}

#[pymodule]
fn skjol_runtime_template(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(run, module)?)?;
    Ok(())
}
