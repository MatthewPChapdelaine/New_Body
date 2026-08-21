"""Surrogate orchestrator: ties the nervous system, patch panel, PoE, and
chassis into a single stationary placing-rig control plane."""

from dataclasses import dataclass, field

from .cat8 import Cat8Link
from .chassis import MiniChassis
from .patch_panel import PatchPanel
from .poe import PoeClass, PoeDelivery, PoeSlice


@dataclass
class Surrogate:
    """The 6-foot physical surrogate shell + VR companion control plane."""

    name: str
    core_platform: str = "Linux Mint Cinnamon"
    vr_integration: str = "VRChat SDK Manual Stack"
    patch_panel: PatchPanel = field(default_factory=PatchPanel)
    chassis: MiniChassis = field(default_factory=MiniChassis)
    poe: dict[str, PoeDelivery] = field(default_factory=dict)

    @classmethod
    def factory_default(cls, name: str = "Surrogate-01") -> "Surrogate":
        def link_factory(port_id: int) -> Cat8Link:
            # Interior runs are contained well under the 30 m geometric limit.
            return Cat8Link(identifier=f"cat8-{port_id:02d}", length_m=4.5)

        panel = PatchPanel.default_layout(link_factory)
        # Each subsystem node draws from its own localized PoE++ line, each
        # capped at the 90 W Type 4 ceiling per the EDD section 5.
        poe = {
            "Head & Sensory Node": PoeDelivery(
                source="PoE++ Injector / Switch in Base",
                slices=[PoeSlice("Head Face-Tracking", 30, 5)],
            ),
            "Upper Torso & Kinetic": PoeDelivery(
                source="PoE++ Injector / Switch in Base",
                slices=[PoeSlice("Expression Servos", 90, 12)],
            ),
            "Lower Base & Rig": PoeDelivery(
                source="PoE++ Injector / Switch in Base",
                slices=[PoeSlice("Rig Encoders", 15, 5)],
            ),
            "Environmental Matrix": PoeDelivery(
                source="PoE++ Injector / Switch in Base",
                slices=[PoeSlice("Cooling Pumps", 90, 12)],
            ),
        }
        return cls(
            name=name,
            patch_panel=panel,
            chassis=MiniChassis(),
            poe=poe,
        )

    def telemetry(self) -> dict:
        total = sum(d.total_watts for d in self.poe.values())
        return {
            "name": self.name,
            "core_platform": self.core_platform,
            "vr_integration": self.vr_integration,
            "ports": len(self.patch_panel.ports),
            "subsystems": self.patch_panel.subsystems(),
            "total_poe_watts": total,
            "poe_ceiling_watts": PoeClass.TYPE_4.max_watts,
        }

    def health_check(self) -> list[str]:
        issues: list[str] = []
        issues.extend(self.patch_panel.validate())
        for delivery in self.poe.values():
            issues.extend(delivery.validate())
        issues.extend(self.chassis.validate())
        return issues

    def is_healthy(self) -> bool:
        return not self.health_check()
