//! Raw binary framing for the surrogate nervous system (Cat-8 link layer).
//!
//! Mirrors `src/new_body/raw.py`. Frames are little-endian, magic-prefixed,
//! and protected by an IEEE 802.3 CRC32 that is byte-compatible with Python's
//! `zlib.crc32` (verified against the `123456789` test vector).

use serde::Serialize;

pub const MAGIC: &[u8; 4] = b"NB0\x01";
pub const VERSION: u8 = 1;

pub const PROTO_CONTROL: u8 = 0;
pub const PROTO_SENSORY: u8 = 1;
pub const PROTO_HAPTIC: u8 = 2;
pub const PROTO_THERMAL: u8 = 3;
pub const PROTO_UPLINK: u8 = 4;
pub const PROTO_BIOMETRIC: u8 = 5; // human body-system telemetry
pub const PROTO_COGNITIVE: u8 = 6; // mind / cognitive-module telemetry

const HEADER_SIZE: usize = 4 + 1 + 1 + 2 + 8 + 2; // magic..payload_len
const MIN_SIZE: usize = HEADER_SIZE + 4; // + crc32

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Frame {
    pub protocol: u8,
    pub port: u16,
    pub timestamp_us: u64,
    pub payload: Vec<u8>,
}

/// IEEE 802.3 CRC32 (reflected, poly 0xEDB88320) — matches `zlib.crc32`.
pub fn crc32(data: &[u8]) -> u32 {
    let mut crc: u32 = 0xFFFF_FFFF;
    for &byte in data {
        crc ^= byte as u32;
        for _ in 0..8 {
            if crc & 1 != 0 {
                crc = (crc >> 1) ^ 0xEDB8_8320;
            } else {
                crc >>= 1;
            }
        }
    }
    !crc
}

impl Frame {
    pub fn encode(&self) -> Vec<u8> {
        let mut body = Vec::with_capacity(MIN_SIZE + self.payload.len());
        body.extend_from_slice(MAGIC);
        body.push(VERSION);
        body.push(self.protocol);
        body.extend_from_slice(&self.port.to_le_bytes());
        body.extend_from_slice(&self.timestamp_us.to_le_bytes());
        body.extend_from_slice(&(self.payload.len() as u16).to_le_bytes());
        body.extend_from_slice(&self.payload);
        let crc = crc32(&body);
        body.extend_from_slice(&crc.to_le_bytes());
        body
    }

    pub fn decode(data: &[u8]) -> Result<Frame, String> {
        if data.len() < MIN_SIZE {
            return Err("frame too short".into());
        }
        if &data[0..4] != MAGIC {
            return Err(format!("bad magic: {:?}", &data[0..4]));
        }
        if data[4] != VERSION {
            return Err(format!("unsupported version: {}", data[4]));
        }
        let protocol = data[5];
        let port = u16::from_le_bytes([data[6], data[7]]);
        let timestamp_us = u64::from_le_bytes(data[8..16].try_into().unwrap());
        let plen = u16::from_le_bytes([data[16], data[17]]) as usize;
        let body_end = HEADER_SIZE + plen;
        if data.len() < body_end + 4 {
            return Err("truncated payload".into());
        }
        let payload = data[HEADER_SIZE..body_end].to_vec();
        let crc = u32::from_le_bytes(data[body_end..body_end + 4].try_into().unwrap());
        let computed = crc32(&data[..body_end]);
        if computed != crc {
            return Err(format!("crc mismatch: computed {computed:#x} != {crc:#x}"));
        }
        Ok(Frame {
            protocol,
            port,
            timestamp_us,
            payload,
        })
    }

    pub fn size(&self) -> usize {
        self.encode().len()
    }
}

/// Decode a concatenated frame stream, returning decoded frames and any
/// trailing bytes that don't yet form a complete frame.
pub fn decode_stream(buffer: &[u8]) -> Result<(Vec<Frame>, Vec<u8>), String> {
    let mut frames = Vec::new();
    let mut offset = 0;
    let n = buffer.len();
    while offset + MIN_SIZE <= n {
        if &buffer[offset..offset + 4] != MAGIC {
            return Err(format!("bad magic at offset {offset}"));
        }
        let plen = u16::from_le_bytes([buffer[offset + 16], buffer[offset + 17]]) as usize;
        let end = offset + HEADER_SIZE + plen + 4;
        if n < end {
            break;
        }
        frames.push(Frame::decode(&buffer[offset..end])?);
        offset = end;
    }
    Ok((frames, buffer[offset..].to_vec()))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample() -> Frame {
        Frame {
            protocol: PROTO_SENSORY,
            port: 3,
            timestamp_us: 1_234_567,
            payload: vec![0xDE, 0xAD, 0xBE, 0xEF],
        }
    }

    #[test]
    fn roundtrip() {
        let frame = sample();
        let bytes = frame.encode();
        assert_eq!(Frame::decode(&bytes).unwrap(), frame);
    }

    #[test]
    fn crc_mismatch_detected() {
        let mut bytes = sample().encode();
        let last = bytes.len() - 1;
        bytes[last] ^= 0xFF;
        assert!(Frame::decode(&bytes).is_err());
    }

    #[test]
    fn bad_magic_rejected() {
        let mut bytes = sample().encode();
        bytes[0] = 0xFF;
        assert!(Frame::decode(&bytes).is_err());
    }

    #[test]
    fn truncated_payload_rejected() {
        let bytes = sample().encode();
        assert!(Frame::decode(&bytes[..bytes.len() - 2]).is_err());
    }

    #[test]
    fn stream_decode_and_leftover() {
        let a = sample();
        let b = Frame {
            port: 7,
            timestamp_us: 99,
            protocol: PROTO_SENSORY,
            payload: vec![0x01, 0x02],
        };
        let mut buf = a.encode();
        buf.extend_from_slice(&b.encode());
        buf.extend_from_slice(&[0x00, 0x01]); // trailing partial frame
        let (frames, leftover) = decode_stream(&buf).unwrap();
        assert_eq!(frames.len(), 2);
        assert_eq!(frames[0].port, 3);
        assert_eq!(frames[1].port, 7);
        assert_eq!(leftover, vec![0x00, 0x01]);
    }

    #[test]
    fn crc32_parity_with_standard_vector() {
        // CRC32("123456789") == 0xCBF43926 — must match Python's zlib.crc32.
        assert_eq!(crc32(b"123456789"), 0xCBF4_3926);
    }
}
