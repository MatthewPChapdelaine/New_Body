"""Example: an R&D entity registers an experimental sensor suite.

Run with:  PYTHONPATH=src python3 examples/add_research_subsystem.py

This demonstrates that contributors can extend the patch panel WITHOUT editing
core source — only by registering a SubsystemSpec.
"""

from new_body.cat8 import Cat8Link
from new_body.patch_panel import (
    PatchPanel,
    SubsystemSpec,
    register_subsystem,
)
from new_body.surrogate import Surrogate
from new_body.telemetry import render_status


def main() -> None:
    # 1. Declare the new research node.
    register_subsystem(
        SubsystemSpec(
            name="R&D Lidar Array",
            interface_type="Solid-State Lidar + IMU Telemetry",
            protocol="40GBASE-T",
            poe_class="PoE++ Type 4 (Up to 90W)",
            port_range=(13, 14),
        )
    )

    # 2. Build a surrogate whose panel now includes the new node.
    surrogate = Surrogate.factory_default("R&D-Surrogate")
    panel = PatchPanel.default_layout(
        lambda pid: Cat8Link(identifier=f"cat8-{pid:02d}", length_m=3.0)
    )
    surrogate.patch_panel = panel

    # 3. Show it integrated into the live control plane.
    print(render_status(surrogate))
    print()
    print(f"Total subsystems: {len(panel.subsystems())}")
    print(f"New node present : {'R&D Lidar Array' in panel.subsystems()}")


if __name__ == "__main__":
    main()
