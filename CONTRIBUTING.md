# Contributing to New Body

New Body is an open control-plane framework modeling the VR/Physical Surrogate
Robot Infrastructure described in `source.html`. It is built for **Research &
Development entities** to extend: add sensor suites, swap power topologies,
simulate new chassis form factors, or hook the telemetry layer into lab
instrumentation.

## Quick start

```bash
git clone <your-fork>
cd New_Body
make install-dev      # installs the package + pytest, ruff, black
make test             # runs the suite (8+ tests)
make lint             # ruff + black checks
```

Prefer `make` targets; raw equivalents live in `pyproject.toml`.

## How the codebase maps to the design document

| EDD section | Module | Responsibility |
| --- | --- | --- |
| 2. Nervous System | `src/new_body/cat8.py` | Cat-8 S/FTP link model: throughput, latency, EMI, 30 m limit |
| 3. Patch Panel | `src/new_body/patch_panel.py` | 12-port layout + the **extension registry** |
| 4. Mini-Chassis | `src/new_body/chassis.py` | Enclosure, ventilation, ESD grounding |
| 5. PoE++ Delivery | `src/new_body/poe.py` | IEEE 802.3bt Type 4 power-over-data |
| Orchestrator | `src/new_body/surrogate.py` | Wires the above into one control plane |
| Telemetry | `src/new_body/telemetry.py` | Status + health rendering |
| CLI | `src/new_body/cli.py` | `new-body status` / `new-body health` |

## Primary extension point: registering a new subsystem

You do **not** need to edit core files to add a research node. Use the
subsystem registry (see `examples/add_research_subsystem.py`):

```python
from new_body.patch_panel import register_subsystem, SubsystemSpec, PatchPanel
from new_body.cat8 import Cat8Link

register_subsystem(
    SubsystemSpec(
        name="R&D Lidar Array",
        interface_type="Solid-State Lidar + IMU Telemetry",
        protocol="40GBASE-T",
        poe_class="PoE++ Type 4 (Up to 90W)",
        port_range=(13, 14),   # contiguous, non-overlapping ports
    )
)

panel = PatchPanel.default_layout(lambda pid: Cat8Link(f"cat8-{pid:02d}", 3.0))
```

Constraints enforced automatically:

- Port ranges must be `1..48`, `start <= end`.
- Two differently-named specs may **not** overlap port ranges.
- The canonical 12-port base chassis is seeded at import; your spec is
  appended to the registry, so `default_layout` picks it up.

For fully bespoke rigs (non-contiguous maps, simulated harnesses), use
`PatchPanelBuilder` instead of the registry.

## Contribution workflow

1. Fork and create a topic branch (`git checkout -b rd/<short-descriptor>`).
2. Add/extend modules under `src/new_body/`. Keep type hints and docstrings.
3. Add or update tests under `tests/` — new behavior needs coverage.
4. Run `make test lint`. CI runs the same on Python 3.10–3.12.
5. Open a PR using the provided template; describe the R&D motivation, the
   subsystem/interface added, and validation results.

## Coding standards

- **Formatting:** `black` (line-length 88). **Lint:** `ruff` (E, F, I, B, UP, W).
- **Typing:** keep full type hints; the project targets Python 3.10+.
- **Tests:** `pytest`; prefer pure unit tests over integration where possible.
- **Docs:** update `docs/ARCHITECTURE.md` when you change extension points.

## Reporting issues / proposing research

Use the issue templates:

- **Bug report** — unexpected validation/telemetry behavior.
- **R&D proposal** — a new sensor class, power topology, or simulation hook
  you intend to contribute. Include the motivating use case.

## License

MIT — contributions are accepted under the same license.
