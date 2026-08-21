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
- **`Surrogate`** — the orchestrator. `factory_default()` builds the canonical
  rig; `health_check()` aggregates validation across all layers.

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

## Roadmap (suggested)

- Simulated link congestion / packet-loss model in `Cat8Link`.
- Health history + trend telemetry.
- Adapter to stream `telemetry()` into an external R&D dashboard.
