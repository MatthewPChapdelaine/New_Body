"""Optional Rust-accelerated backend for the New Body control plane.

The Rust extension ``_new_body_rust`` is built separately with maturin and is
NOT required by the pure-Python package. When present, :class:`RustSurrogate`
exposes the same surface as :class:`new_body.surrogate.Surrogate`, so callers
can transparently use the faster Rust core.
"""

try:
    from _new_body_rust import Surrogate as _RustSurrogate

    RUST_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    _RustSurrogate = None
    RUST_AVAILABLE = False


class RustSurrogate:
    """Thin adapter over the PyO3 ``Surrogate`` class."""

    def __init__(self, name: str = "Surrogate-01") -> None:
        if not RUST_AVAILABLE:
            raise RuntimeError(
                "Rust extension not built. Run `maturin develop` in rust/pyext."
            )
        self._inner = _RustSurrogate(name)

    def telemetry(self) -> dict:
        import json

        return json.loads(self._inner.telemetry())

    def health_check(self) -> list[str]:
        return self._inner.health_check()

    def is_healthy(self) -> bool:
        return self._inner.is_healthy()

    def status(self) -> str:
        return self._inner.status()

    def health(self) -> str:
        return self._inner.health()
