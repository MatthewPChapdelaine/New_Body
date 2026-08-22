"""Centralized mini-patch panel marshaling the surrogate's sensory nodes.

Mirrors section 3 of the EDD: a grounded, high-density panel in the lower
structural base frame routing all subsystem nodes over 40GBASE-T.

This module is the primary extension point for R&D contributors. New sensor
suites can be registered without editing core code (see ``register_subsystem``
and ``PatchPanelBuilder``), so research teams can bolt on experimental nodes.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from .cat8 import Cat8Link

LinkFactory = Callable[[int], Cat8Link]

MAX_PORTS = 48  # research rigs may exceed the canonical 12-port base chassis


@dataclass(frozen=True)
class SubsystemSpec:
    """Declarative description of a subsystem node for the patch panel."""

    name: str
    interface_type: str
    protocol: str
    poe_class: str | None
    port_range: tuple[int, int]  # 1-indexed, inclusive

    def __post_init__(self) -> None:
        start, end = self.port_range
        if not (1 <= start <= end <= MAX_PORTS):
            raise ValueError(
                f"{self.name}: invalid port range {self.port_range} "
                f"(must be 1..{MAX_PORTS}, start <= end)"
            )

    @property
    def port_ids(self) -> list[int]:
        start, end = self.port_range
        return list(range(start, end + 1))


_REGISTRY: dict[str, SubsystemSpec] = {}


def register_subsystem(spec: SubsystemSpec) -> None:
    """Register (or overwrite) a subsystem spec in the global registry.

    R&D teams call this at import time to add experimental nodes. Port ranges
    must not overlap with an already-registered, differently-named spec.
    """
    for existing in _REGISTRY.values():
        if existing.name == spec.name:
            continue
        a_start, a_end = existing.port_range
        b_start, b_end = spec.port_range
        if max(a_start, b_start) <= min(a_end, b_end):
            raise ValueError(
                f"Port range {spec.port_range} for '{spec.name}' overlaps "
                f"'{existing.name}' range {existing.port_range}"
            )
    _REGISTRY[spec.name] = spec


def registered_subsystems() -> list[SubsystemSpec]:
    return list(_REGISTRY.values())


def clear_registry() -> None:
    """Reset the registry (primarily for tests)."""
    _REGISTRY.clear()


@dataclass
class PatchPort:
    """A single keystone-terminated port on the mini-patch panel."""

    port_id: int
    subsystem: str
    interface_type: str
    protocol: str
    poe_class: str | None
    link: Cat8Link | None = None

    def __str__(self) -> str:
        poe = self.poe_class or "Unpowered"
        return (
            f"Port {self.port_id:02d} | {self.subsystem} | "
            f"{self.interface_type} | {self.protocol} | {poe}"
        )


# --- Canonical 12-port base chassis (section 3 of the EDD) -----------------
_BASE_SPECS: list[SubsystemSpec] = [
    SubsystemSpec(
        "Head & Sensory Node",
        "High-Definition Face-Tracking Cameras & Spatial Microphones",
        "40GBASE-T",
        "PoE++ Type 4 (<=30W)",
        (1, 2),
    ),
    SubsystemSpec(
        "Upper Torso & Kinetic",
        "Localized Haptic Feedback Arrays & Expression Servo Controllers",
        "40GBASE-T",
        "PoE++ Type 4 (Up to 90W)",
        (3, 6),
    ),
    SubsystemSpec(
        "Lower Base & Rig",
        "Placing Rig Alignment Encoders & Frame Security Interlocks",
        "40GBASE-T",
        "PoE++ Type 4 (<=15W)",
        (7, 8),
    ),
    SubsystemSpec(
        "Environmental Matrix",
        "Liquid-Cooling Thermal Telemetry & Lung-Style Intake Fans",
        "40GBASE-T",
        "PoE++ Type 4 (Up to 90W)",
        (9, 10),
    ),
    SubsystemSpec(
        "External Umbilical",
        "High-Speed Remote Uplink to Dedicated Workstation Hub",
        "40GBASE-T",
        "Unpowered (Data Only)",
        (11, 12),
    ),
]


def seed_base_registry() -> None:
    """(Re)seed the canonical 12-port base chassis into the registry."""
    for spec in _BASE_SPECS:
        _REGISTRY.setdefault(spec.name, spec)


def base_specs() -> list[SubsystemSpec]:
    """Return a fresh list of the canonical 12-port base chassis specs."""
    return list(_BASE_SPECS)


seed_base_registry()


class PatchPanelBuilder:
    """Programmatic builder for custom research rig layouts.

    Use this when an R&D team needs a bespoke panel instead of the registry
    defaults (e.g. simulated harnesses with non-contiguous port maps).
    """

    def __init__(self) -> None:
        self._specs: list[SubsystemSpec] = []

    def add(self, spec: SubsystemSpec) -> "PatchPanelBuilder":
        self._specs.append(spec)
        return self

    def build(self, link_factory: LinkFactory) -> "PatchPanel":
        return PatchPanel.from_specs(self._specs, link_factory)


@dataclass
class PatchPanel:
    """Grounded mini-patch panel housed in the lower base frame."""

    ports: list[PatchPort] = field(default_factory=list)

    @classmethod
    def from_specs(
        cls, specs: Iterable[SubsystemSpec], link_factory: LinkFactory
    ) -> "PatchPanel":
        ports: list[PatchPort] = []
        for spec in specs:
            for pid in spec.port_ids:
                ports.append(
                    PatchPort(
                        port_id=pid,
                        subsystem=spec.name,
                        interface_type=spec.interface_type,
                        protocol=spec.protocol,
                        poe_class=spec.poe_class,
                        link=link_factory(pid),
                    )
                )
        ports.sort(key=lambda p: p.port_id)
        return cls(ports=ports)

    @classmethod
    def default_layout(cls, link_factory: LinkFactory) -> "PatchPanel":
        """Build the canonical 12-port base chassis from the registry."""
        return cls.from_specs(registered_subsystems(), link_factory)

    def port(self, port_id: int) -> PatchPort:
        for p in self.ports:
            if p.port_id == port_id:
                return p
        raise KeyError(f"No port {port_id} on the patch panel")

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
        return "\n".join(f"{p}" for p in self.ports)
