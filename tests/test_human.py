import struct

from new_body.body import BodySystemId, HumanTwin, MindModuleId
from new_body.raw import (
    PROTO_BIOMETRIC,
    PROTO_COGNITIVE,
    decode_frame,
)


def test_factory_default_full_body_and_mind():
    twin = HumanTwin.factory_default("Human-QA")
    # 11 body systems, 10 mind modules
    assert len(twin.systems) == 11
    assert len(twin.mind) == 10
    assert BodySystemId.NERVOUS.value in [s.id for s in twin.systems]
    assert MindModuleId.LANGUAGE.value in [m.id for m in twin.mind]


def test_canonical_twin_is_healthy():
    twin = HumanTwin.factory_default()
    assert twin.is_healthy()
    t = twin.telemetry()
    assert t["overall_status"] == "nominal"
    # base 12 + body organs + mind modules span the patch panel
    assert t["surrogate_ports"] > 12


def test_emit_frames_roundtrip():
    twin = HumanTwin.factory_default()
    frames = twin.emit_frames()
    # every organ (biometric) + mind module (cognitive) emits one frame
    organs = sum(len(s.organs) for s in twin.systems)
    assert len(frames) == organs + len(twin.mind)

    # decode the first biometric frame and confirm it carries f32 vitals
    decoded = decode_frame(frames[0])
    assert decoded.protocol == PROTO_BIOMETRIC
    values = struct.unpack("<" + "f" * (len(decoded.payload) // 4), decoded.payload)
    assert len(values) >= 1

    # a cognitive frame decodes to a single f32 activation
    cog = [f for f in frames if decode_frame(f).protocol == PROTO_COGNITIVE][0]
    dec = decode_frame(cog)
    (act,) = struct.unpack("<f", dec.payload)
    assert 0.0 <= act <= 1.0


def test_out_of_range_detected():
    twin = HumanTwin.factory_default()
    # push a vital out of range and confirm validation flags it
    twin.systems[0].organs[0].vitals[0].value = 999.0
    issues = twin.validate()
    assert any("out of range" in i for i in issues)
    assert not twin.is_healthy()
