//! 3D-printed mini-chassis integration for the lower base frame.
//!
//! Mirrors section 4 of the EDD: dual-lip slide-out rail, hexagonal
//! ventilation lattice, and ESD grounding via a 10AWG copper drain wire.

use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
pub struct MiniChassis {
    pub form_factor_in: u32,
    pub slide_out_rail: bool,
    pub hex_ventilation: bool,
    pub esd_drain_awg: u32,
    pub esd_to_earth: bool,
}

impl Default for MiniChassis {
    fn default() -> Self {
        Self {
            form_factor_in: 10,
            slide_out_rail: true,
            hex_ventilation: true,
            esd_drain_awg: 10,
            esd_to_earth: true,
        }
    }
}

impl MiniChassis {
    pub fn esd_protection_ok(&self) -> bool {
        self.esd_to_earth && self.esd_drain_awg >= 10
    }

    pub fn toolless_access(&self) -> bool {
        self.slide_out_rail
    }

    pub fn thermal_exhaust_ok(&self) -> bool {
        self.hex_ventilation
    }

    pub fn validate(&self) -> Vec<String> {
        let mut issues = Vec::new();
        if !self.esd_protection_ok() {
            issues.push("ESD grounding incomplete - core at risk from static".into());
        }
        if !self.thermal_exhaust_ok() {
            issues.push("Hex ventilation missing - active NIC heat trapped".into());
        }
        issues
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_chassis_valid() {
        assert!(MiniChassis::default().esd_protection_ok());
        assert!(MiniChassis::default().validate().is_empty());
    }
}
