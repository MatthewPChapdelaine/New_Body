# New Body

> VR/Physical Surrogate Robot Infrastructure Framework

A Creative Technological Development Project derived from the Engineering
Design Document (`source.html`). New Body models the physical layer and power
distribution topology of a 6-foot physical surrogate shell operating inside a
stationary placing rig, bridging high-density sensory arrays with an
internal liquid-cooled processing core running localized logic and the
VRChat SDK manual pipeline.

It is implemented as a Python control-plane library plus a CLI that emulates
and validates the four pillars of the design:

| Section | Module | What it models |
| --- | --- | --- |
| 2. Nervous System Emulation | `cat8` | Cat-8 S/FTP 40GBASE-T links, sub-ms serialization, EMI isolation, 30 m limit |
| 3. Patch Panel | `patch_panel` | 12-port grounded mini-panel mapping subsystem nodes to ports |
| 4. Mini-Chassis | `chassis` | 3D-printed enclosure, slide-out rail, hex ventilation, ESD drain |
| 5. PoE++ Delivery | `poe` | IEEE 802.3bt Type 4 (90 W) power-over-data, splitter rails |

> **Rust core:** the same control plane is implemented in Rust under
> [`rust/`](rust/) (`new-body-core` library + `new-body-rs` CLI), with an
> optional PyO3 extension exposing it to Python. See
> [`rust/README.md`](rust/README.md).

## Layout

```
src/new_body/
    cat8.py          # Nervous system emulation (Cat-8 array)
    patch_panel.py   # 12-port mini-patch panel
    poe.py           # PoE++ IEEE 802.3bt power delivery
    chassis.py       # 3D-printed mini-chassis integration
    surrogate.py     # Orchestrator wiring everything together
    telemetry.py     # Status + health rendering
    cli.py           # Command-line interface
tests/               # pytest suite
```

## Install

```bash
pip install -e .
```

## Usage

```bash
# Full infrastructure status (layout + PoE delivery path)
new-body --name Surrogate-01 status

# Health check across links, power, and ESD
new-body health

# Encode + decode a sample raw Cat-8 frame
new-body frame

# Emulate the full human body & mind as a structural digital twin
new-body human

# Rust CLI equivalent
new-body-rs human
```

## Library

```python
from new_body.surrogate import Surrogate

s = Surrogate.factory_default("Surrogate-01")
print(s.telemetry())
print(s.health_check())   # [] when nominal
```

### Human body & mind digital twin

`new_body.body` extends the surrogate control plane into an 11-system,
10-module anatomical + cognitive model. Each organ and mind module is bound to
a Cat-8 link on the research rig (ports 13+) and can be serialized into the raw
binary link layer (`PROTO_BIOMETRIC` / `PROTO_COGNITIVE`).

```python
from new_body.body import HumanTwin

twin = HumanTwin.factory_default("Human-01")
print(twin.summary())          # body systems, mind modules, status
print(twin.is_healthy())       # True for the canonical twin
frames = twin.emit_frames()    # raw Cat-8 frames over the link layer
```

The Rust core mirrors this exactly (`new_body_core::body::HumanTwin`).

## Tests

```bash
pytest
```

## Contributing

New Body is built for **Research & Development entities** to extend. Add sensor
suites, power topologies, or chassis variants without touching core code via the
subsystem registry — see [`CONTRIBUTING.md`](CONTRIBUTING.md),
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), and
[`examples/add_research_subsystem.py`](examples/add_research_subsystem.py).

```bash
make install-dev   # package + pytest, ruff, black
make test          # run the suite
make lint          # ruff + black
```

CI runs `ruff`, `black`, and `pytest` on Python 3.10–3.12, plus `cargo test`,
`clippy`, and `rustfmt` on the Rust workspace.

### Rust core

```bash
cargo test --manifest-path rust/Cargo.toml          # library + CLI tests
cargo run  --manifest-path rust/cli/Cargo.toml --bin new-body-rs -- status
```

Optional Python acceleration via PyO3 (see [`rust/README.md`](rust/README.md)):

```bash
cd rust/pyext && maturin develop
python -c "from new_body._rust import RustSurrogate, RUST_AVAILABLE; print(RUST_AVAILABLE)"
```

