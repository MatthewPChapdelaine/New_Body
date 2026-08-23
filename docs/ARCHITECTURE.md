# Architecture

New Body models the surrogate infrastructure from `source.html` as a small,
typed, dependency-free Python control plane. The design goal is **extension,
not implementation**: R&D entities should be able to add sensor suites, power
topologies, and chassis variants without forking core logic.

## Layered model

```
              ┌─────────────────────────────────────────┐
              │              Surrogate                   │   surrogate.py
              │   orchestrates + health_check()          │
              └───────────────┬───────────────┬──────────┘
                  ┌───────────┴────────┐  ┌───┴───────────────┐
                  │   PatchPanel       │  │  PoeDelivery      │   patch_panel.py
                  │   (registry)       │  │  (per node)       │   poe.py
                  └─────────┬──────────┘  └───────────────────┘
                       ┌────┴─────┐
                       │ Cat8Link │                                cat8.py
                       └──────────┘
              ┌─────────────────────────────────────────┐
              │   MiniChassis (ESD / vent / rail)        │   chassis.py
              └─────────────────────────────────────────┘

   telemetry.py  → status/health rendering      cli.py → new-body status|health
```

## Core entities

- **`Cat8Link`** — a single S/FTP Cat-8 link. Computes effective throughput
  (down-negotiates 40→10 Gbps past 30 m), serialization latency, and EMI
  isolation. Pure data; no I/O.
- **`SubsystemSpec` / `PatchPanel`** — declarative subsystem description and
  the panel that instantiates `PatchPort`s from specs.
- **`PoeDelivery` / `PoeSlice`** — per-node IEEE 802.3bt Type 4 power, capped
  at 90 W per line with 5 V / 12 V regulated rails.
- **`MiniChassis`** — enclosure properties: slide-out rail, hex ventilation,
  ESD drain-to-earth.
- **`visualize`** — `render_explorer()` / `write_explorer()` turn a `Surrogate`
  (and optional `HumanTwin`) into a self-contained interactive HTML page
  (clickable topology + Cat-8 / PoE++ calculators + tables). Exposed as
  `new-body explore`; the generated page runs from `file://` with no build step.
- **`Surrogate`** — the orchestrator. `factory_default()` builds the canonical
  rig; `health_check()` aggregates validation across all layers.
- **`HumanTwin`** (`body.py` / `body.rs`) — a structural digital twin of the
  full human body and mind. `factory_default()` wraps a `Surrogate`, wires 11
  body systems (15 organs) and 10 cognitive modules onto Cat-8 links starting at
  port 13, and exposes `validate()` / `is_healthy()` / `telemetry()` /
  `emit_frames()` (raw `PROTO_BIOMETRIC` / `PROTO_COGNITIVE` frames).

## Human body & mind digital twin

`new_body.body` lifts the surrogate control plane into an anatomical + cognitive
model. It is a *structural* twin (ontology + state + telemetry + validation +
raw-binary serialization), not a real-time physiological simulation.

- 11 body systems (`BodySystemId`): integumentary, skeletal, muscular, nervous,
  endocrine, cardiovascular, lymphatic, respiratory, digestive, urinary,
  reproductive. Each organ carries biometrics (`Vital`) with clinical ranges.
- 10 mind modules (`MindModuleId`): perception, attention, memory, learning,
  emotion, executive, language, motor, consciousness, social — each linked to a
  supporting body system.
- **Human nature**, encoded as 33 `NatureConstruct`s across 5 groups. The first
  group, **Instinct**, is the survival/reflexive bedrock — fight, flight, freeze,
  seeking, attachment, nurturance, etc. — encoded directly as the surrogate's
  instinctual substrate; the remaining groups layer temperament (Big Five),
  value orientation, moral foundations, and higher nature on top.
- Every organ/module/nature facet is bound to a Cat-8 link on the research rig
  (ports 13+), so the human emulation rides the same link layer as the EDD base.
- `HumanTwin.emit_frames()` serializes each organ's vitals, each module's
  activation, and each nature construct's weight into raw Cat-8 frames
  (`PROTO_BIOMETRIC` / `PROTO_COGNITIVE` / `PROTO_NATURE`) that decode
  identically in Python and Rust.

The Rust core mirrors this module-for-module (`new_body_core::body`).

## Extension points (for R&D contributors)

### 1. New sensor subsystem (registry)

```python
from new_body.patch_panel import register_subsystem, SubsystemSpec, PatchPanel
from new_body.cat8 import Cat8Link

register_subsystem(SubsystemSpec(
    name="R&D Lidar Array",
    interface_type="Solid-State Lidar + IMU Telemetry",
    protocol="40GBASE-T",
    poe_class="PoE++ Type 4 (Up to 90W)",
    port_range=(13, 14),
))
panel = PatchPanel.default_layout(lambda pid: Cat8Link(f"cat8-{pid:02d}", 3.0))
```

Register at import time. Constraints (validated in `SubsystemSpec.__post_init__`
and `register_subsystem`): ports `1..48`, no overlap between distinct specs.

### 2. Bespoke rig layout (builder)

When the registry defaults don't fit (simulated harnesses, non-contiguous
maps), use `PatchPanelBuilder.add(...).build(link_factory)`.

### 3. New power topology

Subclass or compose `PoeDelivery` / `PoeSlice` with different voltage rails or
a different per-line ceiling, then attach to `Surrogate.poe` keyed by subsystem.

### 4. Telemetry / instrumentation hook

`Surrogate.telemetry()` returns a plain `dict`, and `render_status` produces a
string. Replace `render_status` with a sink that pushes to a lab bus (MQTT,
WebSocket, CSV) — the data model is the contract.

## Validation contract

Every layer exposes `validate() -> list[str]` returning violations (empty =
healthy). `Surrogate.health_check()` concatenates them. Adding a layer? Give it
a `validate()` so the health check covers it automatically.

## Testing

Pure unit tests under `tests/`. Run `make test`. CI exercises Python
3.10–3.12 with `ruff` + `black` + `pytest`.

## Rust core (dual-language)

The same control plane is implemented in Rust under [`rust/`](../rust/) as
`new-body-core` (library) + `new-body-rs` (CLI). The module split mirrors the
Python package (`cat8`, `patch_panel`, `poe`, `chassis`, `surrogate`,
`render`), and uses the identical extension model (registry + builder).

Why two languages:

- **Python** — the primary, dependency-free API and CLI for R&D scripting.
- **Rust** — a high-performance core for hot-path work (bulk telemetry
  aggregation, simulation loops) and a `new-body-rs` standalone CLI.
- **PyO3 bridge** — `rust/pyext` compiles to `_new_body_rust`; the Python shim
  `new_body/_rust.py` exposes `RustSurrogate` with the same surface as
  `new_body.surrogate.Surrogate`, falling back gracefully when the extension
  isn't built (`RUST_AVAILABLE`).

When you change an extension point, update **both** implementations and keep
their tests in parity.

## Roadmap (suggested)

- Simulated link congestion / packet-loss model in `Cat8Link`.
- Health history + trend telemetry.
- Adapter to stream `telemetry()` into an external R&D dashboard.
