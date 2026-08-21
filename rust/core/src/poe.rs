//! PoE++ (IEEE 802.3bt Type 4) power delivery over Cat-8 data lines.
//!
//! Mirrors section 5 of the EDD: layered power over data, kinetic servo drive
//! isolation, environmental loop decoupling, and drop-down voltage regulation.

use serde::Serialize;

#[derive(Debug, Clone, Copy, Serialize)]
pub enum PoeClass {
    Type4,
}

impl PoeClass {
    pub fn max_watts(self) -> f64 {
        90.0
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct PoeSlice {
    pub name: String,
    pub allocated_watts: f64,
    pub target_voltage: u8,
}

impl PoeSlice {
    pub fn new(name: &str, allocated_watts: f64, target_voltage: u8) -> Result<Self, String> {
        if allocated_watts > PoeClass::Type4.max_watts() {
            return Err(format!(
                "{}: {allocated_watts}W exceeds {}W PoE++ ceiling",
                name,
                PoeClass::Type4.max_watts()
            ));
        }
        if target_voltage != 5 && target_voltage != 12 {
            return Err("Regulated rails must be 5V or 12V".into());
        }
        Ok(Self {
            name: name.to_string(),
            allocated_watts,
            target_voltage,
        })
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct PoeDelivery {
    pub source: String,
    pub slices: Vec<PoeSlice>,
}

impl PoeDelivery {
    pub fn new(source: &str) -> Self {
        Self {
            source: source.to_string(),
            slices: Vec::new(),
        }
    }

    pub fn with_slice(mut self, slice: PoeSlice) -> Self {
        self.slices.push(slice);
        self
    }

    pub fn total_watts(&self) -> f64 {
        self.slices.iter().map(|s| s.allocated_watts).sum()
    }

    pub fn splitter_ok(&self) -> bool {
        self.total_watts() <= PoeClass::Type4.max_watts()
    }

    pub fn validate(&self) -> Vec<String> {
        let mut issues = Vec::new();
        if !self.splitter_ok() {
            issues.push(format!(
                "Total draw {}W exceeds splitter ceiling 90W",
                self.total_watts()
            ));
        }
        issues
    }

    pub fn diagram(&self) -> String {
        let splitter = " [Localized Terminal Splitter] ";
        let data = "(40 Gbps Raw Data to Node)";
        let power = "(DC Power to Actuators)";
        [
            format!(
                "[{}] ---- (90W Power + 40 Gbps Data over S/FTP Cat-8) ----> [Shielded Keystone]",
                self.source
            ),
            " ".repeat(78) + "|",
            " ".repeat(70) + splitter,
            " ".repeat(70) + "/" + &" ".repeat(23) + "\\",
            " ".repeat(58) + data + "   " + power,
        ]
        .join("\n")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn watt_ceiling_enforced() {
        assert!(PoeSlice::new("over", 95.0, 12).is_err());
    }

    #[test]
    fn total_under_ceiling_ok() {
        let poe = PoeDelivery::new("base").with_slice(PoeSlice::new("a", 90.0, 12).unwrap());
        assert!(poe.total_watts() <= 90.0);
        assert!(poe.splitter_ok());
    }
}
