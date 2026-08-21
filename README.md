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
| 2. Nervous System Emulation | `cat8` | Cat-8 S/FTP 40GBASE-T links, sub-ms serialization, EMI isolation, 30 m geometric limit |
| 3. Patch Panel | `patch_panel` | 12-port grounded mini-panel mapping subsystem nodes to ports |
| 4. Mini-Chassis | `chassis` | 3D-printed enclosure, slide-out rail, hex ventilation, ESD drain |
| 5. PoE++ Delivery | `poe` | IEEE 802.3bt Type 4 (90 W) power-over-data, splitter rails |

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
```

## Library

```python
from new_body.surrogate import Surrogate

s = Surrogate.factory_default("Surrogate-01")
print(s.telemetry())
print(s.health_check())   # [] when nominal
```

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

CI runs `ruff`, `black`, and `pytest` on Python 3.10–3.12.

