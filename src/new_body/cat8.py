"""Nervous System Emulation over a Category 8 (Cat-8) copper topology.

Mirrors section 2 of the EDD: high-frequency 40GBASE-T deployment with
sub-millisecond sensory serialization, S/FTP EMI isolation, and strict
geometric distance containment.
"""

from dataclasses import dataclass

CAT8_MAX_THROUGHPUT_GBPS = 40
CAT8_MAX_BUS_MHZ = 2000
CAT8_MAX_DISTANCE_M = 30
POE_DISTANCE_DOWN_NEGOTIATION_M = 30


@dataclass(frozen=True)
class Cat8Link:
    """A single S/FTP Cat-8 link in the surrogate nervous system."""

    identifier: str
    length_m: float
    shielded: bool = True

    def effective_throughput_gbps(self) -> float:
        """Return negotiated throughput, down-negotiating past 30 m."""
        if self.length_m > CAT8_MAX_DISTANCE_M:
            return 10.0
        return CAT8_MAX_THROUGHPUT_GBPS

    def serialization_latency_us(self, payload_bytes: int) -> float:
        """Serialization latency in microseconds at the effective rate."""
        gbps = self.effective_throughput_gbps()
        bits = payload_bytes * 8
        seconds = bits / (gbps * 1_000_000_000)
        return seconds * 1_000_000

    def emi_isolation_ok(self, adjacent_pump_active: bool) -> bool:
        """S/FTP construction blocks EMI from liquid-cooling pumps."""
        if not self.shielded:
            return False
        return True

    def within_geometric_limit(self) -> bool:
        return self.length_m <= CAT8_MAX_DISTANCE_M

    def validate(self) -> list[str]:
        """Return a list of validation violations (empty when healthy)."""
        issues: list[str] = []
        if not self.within_geometric_limit():
            issues.append(
                f"{self.identifier}: length {self.length_m}m exceeds "
                f"{CAT8_MAX_DISTANCE_M}m limit (down-negotiates to 10 Gbps)"
            )
        if not self.shielded:
            issues.append(f"{self.identifier}: unshielded pair, EMI corruption risk")
        return issues
