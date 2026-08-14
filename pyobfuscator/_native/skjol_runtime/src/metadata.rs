use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NativeMetadata {
    pub created: String,
    pub license: String,
    pub python_version: String,
    pub source_hash: String,
    pub expiration: Option<String>,
    pub machines: Vec<String>,
    pub domains: Vec<String>,
    pub anti_debug: bool,
}

impl NativeMetadata {
    pub fn parse(data: &[u8]) -> Result<Self, String> {
        let metadata: Self = serde_json::from_slice(data)
            .map_err(|error| format!("invalid native metadata: {error}"))?;
        metadata.validate()?;
        Ok(metadata)
    }

    pub fn enforce(&self, py: Python<'_>) -> PyResult<()> {
        if self.expiration.is_some() {
            return Err(PyRuntimeError::new_err(
                "native expiration policy is not implemented yet",
            ));
        }
        if !self.machines.is_empty() {
            return Err(PyRuntimeError::new_err(
                "native machine-binding policy is not implemented yet",
            ));
        }
        if !self.domains.is_empty() {
            return Err(PyRuntimeError::new_err(
                "native domain policy is not implemented yet",
            ));
        }
        if self.anti_debug && !py.import("sys")?.call_method0("gettrace")?.is_none() {
            return Err(PyRuntimeError::new_err("debug environment detected"));
        }
        Ok(())
    }

    fn validate(&self) -> Result<(), String> {
        if self.created.len() > 128 || self.license.len() > 4096 {
            return Err("native metadata text exceeds the supported limit".into());
        }
        if self.python_version.len() > 16 || self.source_hash.len() != 64 {
            return Err("invalid native metadata identity fields".into());
        }
        Ok(())
    }
}
