use std::os::raw::c_char;

use pyo3::exceptions::{PyRuntimeError, PyTypeError};
use pyo3::ffi;
use pyo3::prelude::*;

pub fn execute_marshaled(py: Python<'_>, name: &str, marshaled: &[u8]) -> PyResult<()> {
    let module = py.import(name)?;
    let globals = module.dict();

    // SAFETY: `marshaled` remains alive for the call, its length fits Py_ssize_t,
    // and the returned new reference is immediately owned and decref'd below.
    let code = unsafe {
        ffi::PyMarshal_ReadObjectFromString(
            marshaled.as_ptr().cast::<c_char>(),
            marshaled
                .len()
                .try_into()
                .map_err(|_| PyRuntimeError::new_err("marshalled code is too large"))?,
        )
    };
    if code.is_null() {
        return Err(PyErr::fetch(py));
    }

    // SAFETY: `code` is a non-null owned reference returned by CPython.
    let is_code = unsafe { ffi::PyCode_Check(code) } != 0;
    if !is_code {
        // SAFETY: release the owned reference exactly once on the validation failure path.
        unsafe { ffi::Py_DecRef(code) };
        return Err(PyTypeError::new_err(
            "native payload did not decode to a Python code object",
        ));
    }

    // SAFETY: `code` is a validated code object and both mappings are live module dictionaries.
    let result = unsafe { ffi::PyEval_EvalCode(code, globals.as_ptr(), globals.as_ptr()) };
    // SAFETY: release the owned code reference after evaluation on every result path.
    unsafe { ffi::Py_DecRef(code) };
    if result.is_null() {
        return Err(PyErr::fetch(py));
    }
    // SAFETY: `result` is a non-null new reference returned by CPython.
    unsafe { ffi::Py_DecRef(result) };
    Ok(())
}
