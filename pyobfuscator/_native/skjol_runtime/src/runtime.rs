use std::io::Read;

use base64::Engine;
use base64::engine::general_purpose::STANDARD;
use flate2::read::ZlibDecoder;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use zeroize::Zeroizing;

use crate::artifact::Artifact;
use crate::cpython;
use crate::crypto;
use crate::metadata::NativeMetadata;
use crate::root_key::ROOT_KEY;

const MAX_MARSHALLED_LENGTH: u64 = 64 * 1024 * 1024;

pub fn run(py: Python<'_>, name: &str, payload: &[u8]) -> PyResult<()> {
    let encoded = STANDARD
        .decode(payload)
        .map_err(|_| PyRuntimeError::new_err("invalid native artifact base64"))?;
    let artifact = Artifact::parse(&encoded).map_err(PyRuntimeError::new_err)?;
    validate_python_version(py, &artifact)?;

    let plaintext = crypto::decrypt(
        &ROOT_KEY,
        &artifact.artifact_id,
        &artifact.nonce,
        artifact.header,
        artifact.ciphertext,
    )
    .map_err(PyRuntimeError::new_err)?;
    if artifact.metadata_length > plaintext.len() {
        return Err(PyRuntimeError::new_err(
            "native metadata length exceeds decrypted payload",
        ));
    }
    let metadata = NativeMetadata::parse(&plaintext[..artifact.metadata_length])
        .map_err(PyRuntimeError::new_err)?;
    metadata.enforce(py)?;

    let mut marshaled = Zeroizing::new(Vec::new());
    ZlibDecoder::new(&plaintext[artifact.metadata_length..])
        .take(MAX_MARSHALLED_LENGTH + 1)
        .read_to_end(&mut marshaled)
        .map_err(|error| {
            PyRuntimeError::new_err(format!("native decompression failed: {error}"))
        })?;
    if marshaled.len() as u64 > MAX_MARSHALLED_LENGTH {
        return Err(PyRuntimeError::new_err(
            "native decompressed payload exceeds the supported limit",
        ));
    }
    cpython::execute_marshaled(py, name, &marshaled)
}

fn validate_python_version(py: Python<'_>, artifact: &Artifact<'_>) -> PyResult<()> {
    let version = py.import("sys")?.getattr("version_info")?;
    let major: u8 = version.getattr("major")?.extract()?;
    let minor: u8 = version.getattr("minor")?.extract()?;
    if (major, minor) != (artifact.python_major, artifact.python_minor) {
        return Err(PyRuntimeError::new_err(format!(
            "native artifact requires CPython {}.{}, running {major}.{minor}",
            artifact.python_major, artifact.python_minor
        )));
    }
    Ok(())
}
