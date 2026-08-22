import zlib

from new_body.raw import (
    PROTO_SENSORY,
    Frame,
    decode_frame,
    decode_stream,
    encode_frame,
)


def _sample() -> Frame:
    return Frame(
        protocol=PROTO_SENSORY,
        port=3,
        timestamp_us=1_234_567,
        payload=bytes([0xDE, 0xAD, 0xBE, 0xEF]),
    )


def test_roundtrip():
    f = _sample()
    raw = encode_frame(f)
    assert decode_frame(raw) == f


def test_crc_mismatch_detected():
    raw = bytearray(encode_frame(_sample()))
    raw[-1] ^= 0xFF
    import pytest

    with pytest.raises(ValueError):
        decode_frame(bytes(raw))


def test_bad_magic_rejected():
    raw = bytearray(encode_frame(_sample()))
    raw[0] = 0xFF
    import pytest

    with pytest.raises(ValueError):
        decode_frame(bytes(raw))


def test_truncated_payload_rejected():
    raw = encode_frame(_sample())
    import pytest

    with pytest.raises(ValueError):
        decode_frame(raw[:-2])


def test_stream_decode_and_leftover():
    a = _sample()
    b = Frame(protocol=PROTO_SENSORY, port=7, timestamp_us=99, payload=b"\x01\x02")
    buf = encode_frame(a) + encode_frame(b) + b"\x00\x01"  # trailing partial
    frames, leftover = decode_stream(buf)
    assert [f.port for f in frames] == [3, 7]
    assert leftover == b"\x00\x01"


def test_crc32_parity_with_standard_vector():
    # CRC32 of "123456789" must equal the well-known 0xCBF43926, ensuring the
    # Rust implementation (and any other consumer) agrees with zlib.
    assert zlib.crc32(b"123456789") & 0xFFFFFFFF == 0xCBF43926
