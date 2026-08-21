"""PoE++ (IEEE 802.3bt Type 4) power delivery over Cat-8 data lines.

Mirrors section 5 of the EDD: layered power over data, kinetic servo drive
isolation, environmental loop decoupling, and drop-down voltage regulation.
"""

from dataclasses import dataclass
from enum import Enum


class PoeClass(str, Enum):
    TYPE_4 = "PoE++ Type 4"

    @property
    def max_watts(self) -> float:
        return 90.0


@dataclass
class PoeSlice:
    """A localized power slice carved from a PoE++ line."""

    name: str
    allocated_watts: float
    target_voltage: int  # 5 or 12 V regulated rail

    def __post_init__(self) -> None:
        if self.allocated_watts > PoeClass.TYPE_4.max_watts:
            raise ValueError(
                f"{self.name}: {self.allocated_watts}W exceeds "
                f"{PoeClass.TYPE_4.max_watts}W PoE++ ceiling"
            )
        if self.target_voltage not in (5, 12):
            raise ValueError("Regulated rails must be 5V or 12V")


@dataclass
class PoeDelivery:
    """Power delivery protocol for a subsystem node."""

    source: str  # e.g. "PoE++ Injector / Switch in Base"
    slices: list[PoeSlice] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.slices = self.slices or []

    @property
    def total_watts(self) -> float:
        return sum(s.allocated_watts for s in self.slices)

    def splitter_ok(self) -> bool:
        """Terminal splitter keeps data and power paths independent."""
        return self.total_watts <= PoeClass.TYPE_4.max_watts

    def diagram(self) -> str:
        splitter = " [Localized Terminal Splitter] "
        data = "(40 Gbps Raw Data to Node)"
        power = "(DC Power to Actuators)"
        lines = [
            f"[{self.source}] ---- (90W Power + 40 Gbps Data over S/FTP Cat-8) ----> [Shielded Keystone]",
            " " * 78 + "|",
            " " * 70 + splitter,
            " " * 70 + "/" + " " * 23 + "\\",
            " " * 58 + data + "   " + power,
        ]
        return "\n".join(lines)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.splitter_ok():
            issues.append(
                f"Total draw {self.total_watts}W exceeds splitter ceiling 90W"
            )
        return issues
