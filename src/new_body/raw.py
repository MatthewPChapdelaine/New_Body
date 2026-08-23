"""Raw binary framing for the surrogate nervous system (Cat-8 link layer).

Encodes sensory/control frames into a compact, checksummed byte layout that
mimics the sub-millisecond serialization described in the EDD section 2. Pure
stdlib (``struct`` + ``zlib``) — no external dependencies, and CRC32 is
byte-compatible with the Rust ``new-body-core`` implementation.

Frame layout (little-endian)::

    +--------+---------+----------+------+------+-------------+----------+---------+
    | magic  | version | protocol | port |  ts  | payload_len | payload |  crc32  |
    | 4s     | B       | B        | H    |  Q   | H           | ...      | I       |
    +--------+---------+----------+------+------+-------------+----------+---------+
"""

import struct
import zlib
from dataclasses import dataclass

MAGIC = b"NB0\x01"
VERSION = 1

# Protocol identifiers (subsystem link classes).
PROTO_CONTROL = 0
PROTO_SENSORY = 1
PROTO_HAPTIC = 2
PROTO_THERMAL = 3
PROTO_UPLINK = 4
PROTO_BIOMETRIC = 5  # human body-system telemetry
PROTO_COGNITIVE = 6  # mind / cognitive-module telemetry
PROTO_NATURE = 7  # human nature constructs (drives, values, moral, higher)

_HEADER = struct.Struct("<4sBBHQH")  # magic, version, protocol, port, ts, payload_len
_CRC = struct.Struct("<I")

# Minimum on-wire size: header + crc (no payload).
_MIN_SIZE = _HEADER.size + _CRC.size


@dataclass
class Frame:
    """A single Cat-8 link-layer frame."""

    protocol: int
    port: int
    timestamp_us: int
    payload: bytes

    def __bytes__(self) -> bytes:
        return encode_frame(self)

    @property
    def size(self) -> int:
        return len(encode_frame(self))


def encode_frame(frame: Frame) -> bytes:
    if not 0 <= frame.protocol <= 0xFF:
        raise ValueError("protocol out of range")
    if not 0 <= frame.port <= 0xFFFF:
        raise ValueError("port out of range")
    header = _HEADER.pack(
        MAGIC,
        VERSION,
        frame.protocol,
        frame.port,
        frame.timestamp_us,
        len(frame.payload),
    )
    body = header + frame.payload
    crc = zlib.crc32(body) & 0xFFFFFFFF
    return body + _CRC.pack(crc)


def decode_frame(data: bytes) -> Frame:
    if len(data) < _MIN_SIZE:
        raise ValueError("frame too short")
    magic, version, protocol, port, ts, plen = _HEADER.unpack_from(data, 0)
    if magic != MAGIC:
        raise ValueError(f"bad magic: {magic!r}")
    if version != VERSION:
        raise ValueError(f"unsupported version: {version}")
    expected = _HEADER.size + plen + _CRC.size
    if len(data) < expected:
        raise ValueError("truncated payload")
    payload = data[_HEADER.size : _HEADER.size + plen]
    (crc,) = _CRC.unpack_from(data, _HEADER.size + plen)
    body = data[: _HEADER.size + plen]
    if (zlib.crc32(body) & 0xFFFFFFFF) != crc:
        raise ValueError("crc mismatch")
    return Frame(protocol=protocol, port=port, timestamp_us=ts, payload=payload)


def decode_stream(buffer: bytes) -> tuple[list[Frame], bytes]:
    """Decode a concatenated frame stream.

    Returns the decoded frames and any trailing bytes that do not yet form a
    complete frame (re-feed them once more data arrives).
    """
    frames: list[Frame] = []
    offset = 0
    n = len(buffer)
    while offset + _MIN_SIZE <= n:
        magic, _version, _proto, _port, _ts, plen = _HEADER.unpack_from(buffer, offset)
        if magic != MAGIC:
            raise ValueError(f"bad magic at offset {offset}")
        end = offset + _HEADER.size + plen + _CRC.size
        if n < end:
            break  # need more bytes
        frames.append(decode_frame(buffer[offset:end]))
        offset = end
    return frames, buffer[offset:]
