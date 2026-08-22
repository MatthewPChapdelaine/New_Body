//! Surrogate orchestrator: ties the nervous system, patch panel, PoE, and
//! chassis into a single stationary placing-rig control plane.

use std::collections::HashMap;

use serde::Serialize;

use crate::cat8::Cat8Link;
use crate::chassis::MiniChassis;
use crate::patch_panel::PatchPanel;
use crate::poe::{PoeClass, PoeDelivery, PoeSlice};

#[derive(Debug, Clone, Serialize)]
pub struct Telemetry {
    pub name: String,
    pub core_platform: String,
    pub vr_integration: String,
    pub ports: usize,
    pub subsystems: Vec<String>,
    pub total_poe_watts: f64,
    pub poe_ceiling_watts: f64,
}

#[derive(Debug, Clone, Serialize)]
pub struct Surrogate {
    pub name: String,
    pub core_platform: String,
    pub vr_integration: String,
    pub patch_panel: PatchPanel,
    pub chassis: MiniChassis,
    pub poe: HashMap<String, PoeDelivery>,
}

impl Surrogate {
    pub fn factory_default(name: &str) -> Self {
        let link_factory = |pid: u32| Cat8Link::new(format!("cat8-{pid:02}"), 4.5);
        let patch_panel = PatchPanel::default_layout(link_factory);

        let mut poe = HashMap::new();
        poe.insert(
            "Head & Sensory Node".to_string(),
            PoeDelivery::new("PoE++ Injector / Switch in Base")
                .with_slice(PoeSlice::new("Head Face-Tracking", 30.0, 5).unwrap()),
        );
        poe.insert(
            "Upper Torso & Kinetic".to_string(),
            PoeDelivery::new("PoE++ Injector / Switch in Base")
                .with_slice(PoeSlice::new("Expression Servos", 90.0, 12).unwrap()),
        );
        poe.insert(
            "Lower Base & Rig".to_string(),
            PoeDelivery::new("PoE++ Injector / Switch in Base")
                .with_slice(PoeSlice::new("Rig Encoders", 15.0, 5).unwrap()),
        );
        poe.insert(
            "Environmental Matrix".to_string(),
            PoeDelivery::new("PoE++ Injector / Switch in Base")
                .with_slice(PoeSlice::new("Cooling Pumps", 90.0, 12).unwrap()),
        );

        Self {
            name: name.to_string(),
            core_platform: "Linux Mint Cinnamon".to_string(),
            vr_integration: "VRChat SDK Manual Stack".to_string(),
            patch_panel,
            chassis: MiniChassis::default(),
            poe,
        }
    }

    pub fn telemetry(&self) -> Telemetry {
        let total: f64 = self.poe.values().map(|d| d.total_watts()).sum();
        Telemetry {
            name: self.name.clone(),
            core_platform: self.core_platform.clone(),
            vr_integration: self.vr_integration.clone(),
            ports: self.patch_panel.ports.len(),
            subsystems: self.patch_panel.subsystems(),
            total_poe_watts: total,
            poe_ceiling_watts: PoeClass::Type4.max_watts(),
        }
    }

    pub fn health_check(&self) -> Vec<String> {
        let mut issues = Vec::new();
        issues.extend(self.patch_panel.validate());
        for delivery in self.poe.values() {
            issues.extend(delivery.validate());
        }
        issues.extend(self.chassis.validate());
        issues
    }

    pub fn is_healthy(&self) -> bool {
        self.health_check().is_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn factory_default_healthy() {
        let _guard = crate::patch_panel::REGISTRY_TEST_LOCK.lock().unwrap();
        let s = Surrogate::factory_default("Surrogate-01");
        assert!(s.is_healthy());
        assert_eq!(s.telemetry().ports, 12);
    }
}
