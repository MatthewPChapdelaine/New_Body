"""3D-printed mini-chassis integration for the lower base frame.

Mirrors section 4 of the EDD: dual-lip slide-out rail, hexagonal ventilation
lattice, and ESD grounding via a 10AWG copper drain wire to earth ground.
"""

from dataclasses import dataclass


@dataclass
class MiniChassis:
    """Custom 10-inch form-factor enclosure integrated into the base frame."""

    form_factor_in: int = 10
    slide_out_rail: bool = True
    hex_ventilation: bool = True
    esd_drain_awg: int = 10
    esd_to_earth: bool = True

    def esd_protection_ok(self) -> bool:
        """Static routed to earth ground through metal backing bar + drain wire."""
        return self.esd_to_earth and self.esd_drain_awg >= 10

    def toolless_access(self) -> bool:
        return self.slide_out_rail

    def thermal_exhaust_ok(self) -> bool:
        return self.hex_ventilation

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.esd_protection_ok():
            issues.append("ESD grounding incomplete - core at risk from static")
        if not self.thermal_exhaust_ok():
            issues.append("Hex ventilation missing - active NIC heat trapped")
        return issues
