//! PyO3 binding: exposes the Rust `Surrogate` control plane to Python.
//!
//! Build with maturin (`maturin develop` from `rust/pyext`), which produces the
//! `_new_body_rust` extension module. The Python `new_body._rust` shim imports
//! it and falls back to the pure-Python implementation if it isn't built.

use new_body_core::render;
use new_body_core::surrogate::Surrogate as CoreSurrogate;
use pyo3::prelude::*;

#[pyclass]
struct Surrogate {
    inner: CoreSurrogate,
}

#[pymethods]
impl Surrogate {
    #[new]
    #[pyo3(signature = (name = "Surrogate-01"))]
    fn new(name: &str) -> Self {
        Self {
            inner: CoreSurrogate::factory_default(name),
        }
    }

    /// JSON-encoded telemetry dict.
    fn telemetry(&self) -> String {
        serde_json::to_string(&self.inner.telemetry()).unwrap()
    }

    fn health_check(&self) -> Vec<String> {
        self.inner.health_check()
    }

    fn is_healthy(&self) -> bool {
        self.inner.is_healthy()
    }

    fn status(&self) -> String {
        render::render_status(&self.inner)
    }

    fn health(&self) -> String {
        render::render_health(&self.inner)
    }
}

#[pymodule]
fn _new_body_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Surrogate>()?;
    Ok(())
}
