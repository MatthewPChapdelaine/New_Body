//! Nervous System Emulation over a Category 8 (Cat-8) copper topology.
//!
//! Mirrors section 2 of the EDD: high-frequency 40GBASE-T deployment with
//! sub-millisecond sensory serialization, S/FTP EMI isolation, and strict
//! geometric distance containment.

use serde::Serialize;

pub const CAT8_MAX_THROUGHPUT_GBPS: f64 = 40.0;
pub const CAT8_MAX_BUS_MHZ: f64 = 2000.0;
pub const CAT8_MAX_DISTANCE_M: f64 = 30.0;

#[derive(Debug, Clone, Serialize)]
pub struct Cat8Link {
    pub identifier: String,
    pub length_m: f64,
    pub shielded: bool,
}

impl Cat8Link {
    pub fn new(identifier: impl Into<String>, length_m: f64) -> Self {
        Self {
            identifier: identifier.into(),
            length_m,
            shielded: true,
        }
    }

    /// Negotiated throughput, down-negotiating to 10 Gbps past 30 m.
    pub fn effective_throughput_gbps(&self) -> f64 {
        if self.length_m > CAT8_MAX_DISTANCE_M {
            10.0
        } else {
            CAT8_MAX_THROUGHPUT_GBPS
        }
    }

    /// Serialization latency in microseconds at the effective rate.
    pub fn serialization_latency_us(&self, payload_bytes: usize) -> f64 {
        let gbps = self.effective_throughput_gbps();
        let bits = payload_bytes as f64 * 8.0;
        let seconds = bits / (gbps * 1e9);
        seconds * 1e6
    }

    /// S/FTP construction blocks EMI from liquid-cooling pumps.
    pub fn emi_isolation_ok(&self, _adjacent_pump_active: bool) -> bool {
        self.shielded
    }

    pub fn within_geometric_limit(&self) -> bool {
        self.length_m <= CAT8_MAX_DISTANCE_M
    }

    pub fn validate(&self) -> Vec<String> {
        let mut issues = Vec::new();
        if !self.within_geometric_limit() {
            issues.push(format!(
                "{}: length {}m exceeds {}m limit (down-negotiates to 10 Gbps)",
                self.identifier, self.length_m, CAT8_MAX_DISTANCE_M
            ));
        }
        if !self.shielded {
            issues.push(format!(
                "{}: unshielded pair, EMI corruption risk",
                self.identifier
            ));
        }
        issues
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn full_rate_within_limit() {
        let link = Cat8Link::new("x", 20.0);
        assert_eq!(link.effective_throughput_gbps(), 40.0);
        assert!(link.within_geometric_limit());
    }

    #[test]
    fn down_negotiation_over_limit() {
        let link = Cat8Link::new("x", 45.0);
        assert_eq!(link.effective_throughput_gbps(), 10.0);
        assert!(!link.within_geometric_limit());
    }

    #[test]
    fn sub_millisecond_serialization() {
        let link = Cat8Link::new("x", 5.0);
        assert!(link.serialization_latency_us(1500) < 1000.0);
    }
}
