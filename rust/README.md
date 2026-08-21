# New Body — Rust Core

A high-performance, dependency-light Rust implementation of the New Body
surrogate control plane (see `../source.html` and the Python package at
`../src/new_body`). The Rust core mirrors the Python module layout so the two
stays in sync, and can be used standalone or as a Python-accelerated backend
via PyO3.

## Layout

```
rust/
  Cargo.toml        # workspace (core + cli)
  core/             # library: cat8, patch_panel, poe, chassis, surrogate, render
  cli/              # `new-body-rs` binary (status / health)
  pyext/            # PyO3 cdylib `_new_body_rust` (standalone workspace)
```

## Build & test

```bash
cargo test --manifest-path rust/Cargo.toml
cargo run  --manifest-path rust/cli/Cargo.toml --bin new-body-rs -- status
cargo run  --manifest-path rust/cli/Cargo.toml --bin new-body-rs -- health
```

Crate-level tests, `clippy`, and `rustfmt` are enforced in CI.

## Extension model (same as Python)

Register a research sensor suite without editing core code:

```rust
use new_body_core::patch_panel::{register_subsystem, SubsystemSpec, PatchPanel};
use new_body_core::cat8::Cat8Link;

register_subsystem(
    SubsystemSpec::new(
        "R&D Lidar Array",
        "Solid-State Lidar + IMU",
        "40GBASE-T",
        Some("PoE++ Type 4 (Up to 90W)"),
        13, 14,
    )
    .unwrap(),
)
.unwrap();

let panel = PatchPanel::default_layout(|pid| Cat8Link::new(format!("cat8-{pid:02}"), 3.0));
```

Constraints (validated): ports `1..48`, `start <= end`, no overlap between
distinct subsystem specs.

## Python binding (optional)

The PyO3 crate builds a `_new_body_rust` extension module. From `rust/pyext`:

```bash
pip install maturin
maturin develop
```

Then from Python:

```python
from new_body._rust import RustSurrogate, RUST_AVAILABLE
if RUST_AVAILABLE:
    s = RustSurrogate("Surrogate-01")
    print(s.status())
```

`new_body._rust.RustSurrogate` exposes the same surface as the pure-Python
`new_body.surrogate.Surrogate`; if the extension isn't built, the import falls
back gracefully (`RUST_AVAILABLE == False`).
