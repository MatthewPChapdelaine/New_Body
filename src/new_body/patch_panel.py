"""Centralized 12-port mini-patch panel marshaling the surrogate's sensory nodes.

Mirrors section 3 of the EDD: a grounded, high-density 12-port panel in the
lower structural base frame routing all subsystem nodes over 40GBASE-T.
"""

from dataclasses import dataclass, field
from typing import Optional

from .cat8 import Cat8Link


@dataclass
class PatchPort:
    """A single keystone-terminated port on the mini-patch panel."""

    port_id: int
    subsystem: str
    interface_type: str
    protocol: str
    poe_class: Optional[str]
    link: Optional[Cat8Link] = None

    def __str__(self) -> str:
        poe = self.poe_class or "Unpowered"
        return (
            f"Port {self.port_id:02d} | {self.subsystem} | "
            f"{self.interface_type} | {self.protocol} | {poe}"
        )


_PROFILE: list[tuple[str, str, str, Optional[str]]] = [
    ("Head & Sensory Node", "High-Definition Face-Tracking Cameras & Spatial Microphones", "40GBASE-T", "PoE++ Type 4 (<=30W)"),
    ("Upper Torso & Kinetic", "Localized Haptic Feedback Arrays & Expression Servo Controllers", "40GBASE-T", "PoE++ Type 4 (Up to 90W)"),
    ("Lower Base & Rig", "Placing Rig Alignment Encoders & Frame Security Interlocks", "40GBASE-T", "PoE++ Type 4 (<=15W)"),
    ("Environmental Matrix", "Liquid-Cooling Thermal Telemetry & Lung-Style Intake Fans", "40GBASE-T", "PoE++ Type 4 (Up to 90W)"),
    ("External Umbilical", "High-Speed Remote Uplink to Dedicated Workstation Hub", "40GBASE-T", "Unpowered (Data Only)"),
]

# Port ranges per subsystem node (1-indexed, inclusive).
_PORT_RANGES: list[tuple[int, int, int]] = [
    (1, 2, 0),
    (3, 6, 1),
    (7, 8, 2),
    (9, 10, 3),
    (11, 12, 4),
]


@dataclass
class PatchPanel:
    """12-port grounded mini-patch panel housed in the lower base frame."""

    ports: list[PatchPort] = field(default_factory=list)

    @classmethod
    def default_layout(cls, link_factory) -> "PatchPanel":
        ports: list[PatchPort] = []
        for start, end, profile_idx in _PORT_RANGES:
            subsystem, iface, proto, poe = _PROFILE[profile_idx]
            for pid in range(start, end + 1):
                link = link_factory(pid)
                ports.append(
                    PatchPort(
                        port_id=pid,
                        subsystem=subsystem,
                        interface_type=iface,
                        protocol=proto,
                        poe_class=poe,
                        link=link,
                    )
                )
        return cls(ports=ports)

    def port(self, port_id: int) -> PatchPort:
        for p in self.ports:
            if p.port_id == port_id:
                return p
        raise KeyError(f"No port {port_id} on the patch panel (1-12)")

    def subsystems(self) -> list[str]:
        seen: list[str] = []
        for p in self.ports:
            if p.subsystem not in seen:
                seen.append(p.subsystem)
        return seen

    def validate(self) -> list[str]:
        issues: list[str] = []
        for p in self.ports:
            if p.link is not None:
                issues.extend(p.link.validate())
        return issues

    def report(self) -> str:
        lines = [f"{p}" for p in self.ports]
        return "\n".join(lines)
