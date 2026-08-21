from new_body.cat8 import Cat8Link
from new_body.chassis import MiniChassis
from new_body.patch_panel import PatchPanel
from new_body.poe import PoeDelivery, PoeSlice
from new_body.surrogate import Surrogate


def test_cat8_throughput_full_within_limit():
    link = Cat8Link(identifier="x", length_m=20)
    assert link.effective_throughput_gbps() == 40
    assert link.within_geometric_limit()


def test_cat8_down_negotiation_over_limit():
    link = Cat8Link(identifier="x", length_m=45)
    assert link.effective_throughput_gbps() == 10
    assert not link.within_geometric_limit()


def test_cat8_serialization_latency_sub_millisecond():
    link = Cat8Link(identifier="x", length_m=5)
    # A 1500-byte frame must serialize in well under 1 ms at 40 Gbps.
    assert link.serialization_latency_us(1500) < 1000


def test_patch_panel_default_layout_has_12_ports():
    panel = PatchPanel.default_layout(lambda pid: Cat8Link(f"cat8-{pid:02d}", 4.5))
    assert len(panel.ports) == 12
    assert panel.subsystems() == [
        "Head & Sensory Node",
        "Upper Torso & Kinetic",
        "Lower Base & Rig",
        "Environmental Matrix",
        "External Umbilical",
    ]


def test_poe_watt_ceiling_enforced():
    import pytest

    with pytest.raises(ValueError):
        PoeSlice("over", 95, 12)


def test_poe_total_under_ceiling():
    poe = PoeDelivery(
        source="base",
        slices=[PoeSlice("a", 90, 12), PoeSlice("b", 0, 5)],
    )
    assert poe.total_watts <= 90
    assert poe.splitter_ok()


def test_chassis_esd_ok():
    assert MiniChassis().esd_protection_ok()


def test_surrogate_factory_default_healthy():
    s = Surrogate.factory_default()
    assert s.is_healthy()
    assert s.telemetry()["ports"] == 12
