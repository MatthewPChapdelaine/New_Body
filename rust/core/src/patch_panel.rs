//! Centralized mini-patch panel marshaling the surrogate's sensory nodes.
//!
//! Mirrors section 3 of the EDD: a grounded, high-density panel in the lower
//! structural base frame routing all subsystem nodes over 40GBASE-T.
//!
//! This module is the primary extension point for R&D contributors: new sensor
//! suites register via [`register_subsystem`] (or a [`PatchPanelBuilder`])
//! without editing core code.

use std::sync::{Mutex, OnceLock};

use serde::Serialize;

use crate::cat8::Cat8Link;

pub const MAX_PORTS: u32 = 48; // research rigs may exceed the 12-port base

#[derive(Debug, Clone, Serialize)]
pub struct SubsystemSpec {
    pub name: String,
    pub interface_type: String,
    pub protocol: String,
    pub poe_class: Option<String>,
    pub port_range: (u32, u32),
}

impl SubsystemSpec {
    pub fn new(
        name: &str,
        interface_type: &str,
        protocol: &str,
        poe_class: Option<&str>,
        start: u32,
        end: u32,
    ) -> Result<Self, String> {
        if !(1 <= start && start <= end && end <= MAX_PORTS) {
            return Err(format!(
                "{name}: invalid port range ({start},{end}) must be 1..{MAX_PORTS}, start<=end"
            ));
        }
        Ok(Self {
            name: name.to_string(),
            interface_type: interface_type.to_string(),
            protocol: protocol.to_string(),
            poe_class: poe_class.map(str::to_string),
            port_range: (start, end),
        })
    }

    pub fn port_ids(&self) -> Vec<u32> {
        (self.port_range.0..=self.port_range.1).collect()
    }
}

static REGISTRY: OnceLock<Mutex<Vec<SubsystemSpec>>> = OnceLock::new();

fn registry() -> &'static Mutex<Vec<SubsystemSpec>> {
    REGISTRY.get_or_init(|| Mutex::new(Vec::new()))
}

/// Canonical 12-port base chassis (section 3 of the EDD).
pub fn base_specs() -> Vec<SubsystemSpec> {
    vec![
        SubsystemSpec::new(
            "Head & Sensory Node",
            "High-Definition Face-Tracking Cameras & Spatial Microphones",
            "40GBASE-T",
            Some("PoE++ Type 4 (<=30W)"),
            1,
            2,
        )
        .unwrap(),
        SubsystemSpec::new(
            "Upper Torso & Kinetic",
            "Localized Haptic Feedback Arrays & Expression Servo Controllers",
            "40GBASE-T",
            Some("PoE++ Type 4 (Up to 90W)"),
            3,
            6,
        )
        .unwrap(),
        SubsystemSpec::new(
            "Lower Base & Rig",
            "Placing Rig Alignment Encoders & Frame Security Interlocks",
            "40GBASE-T",
            Some("PoE++ Type 4 (<=15W)"),
            7,
            8,
        )
        .unwrap(),
        SubsystemSpec::new(
            "Environmental Matrix",
            "Liquid-Cooling Thermal Telemetry & Lung-Style Intake Fans",
            "40GBASE-T",
            Some("PoE++ Type 4 (Up to 90W)"),
            9,
            10,
        )
        .unwrap(),
        SubsystemSpec::new(
            "External Umbilical",
            "High-Speed Remote Uplink to Dedicated Workstation Hub",
            "40GBASE-T",
            None,
            11,
            12,
        )
        .unwrap(),
    ]
}

/// (Re)seed the canonical 12-port base chassis into the registry.
pub fn seed_base_registry() {
    let mut reg = registry().lock().unwrap();
    for spec in base_specs() {
        if !reg.iter().any(|e| e.name == spec.name) {
            reg.push(spec);
        }
    }
}

/// Register (or append) a subsystem spec. Port ranges must not overlap an
/// already-registered, differently-named spec.
pub fn register_subsystem(spec: SubsystemSpec) -> Result<(), String> {
    let mut reg = registry().lock().unwrap();
    for existing in reg.iter() {
        if existing.name == spec.name {
            continue;
        }
        let (a0, a1) = existing.port_range;
        let (b0, b1) = spec.port_range;
        if a0.max(b0) <= a1.min(b1) {
            return Err(format!(
                "Port range {:?} for '{}' overlaps '{}' range {:?}",
                spec.port_range, spec.name, existing.name, existing.port_range
            ));
        }
    }
    reg.push(spec);
    Ok(())
}

pub fn registered_subsystems() -> Vec<SubsystemSpec> {
    registry().lock().unwrap().clone()
}

pub fn clear_registry() {
    registry().lock().unwrap().clear();
}

#[derive(Debug, Clone, Serialize)]
pub struct PatchPort {
    pub port_id: u32,
    pub subsystem: String,
    pub interface_type: String,
    pub protocol: String,
    pub poe_class: Option<String>,
    pub link: Option<Cat8Link>,
}

impl std::fmt::Display for PatchPort {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let poe = self
            .poe_class
            .clone()
            .unwrap_or_else(|| "Unpowered".to_string());
        write!(
            f,
            "Port {:02} | {} | {} | {} | {}",
            self.port_id, self.subsystem, self.interface_type, self.protocol, poe
        )
    }
}

/// Programmatic builder for bespoke research rig layouts.
pub struct PatchPanelBuilder {
    specs: Vec<SubsystemSpec>,
}

impl PatchPanelBuilder {
    pub fn new() -> Self {
        Self { specs: Vec::new() }
    }

    pub fn add_subsystem(mut self, spec: SubsystemSpec) -> Self {
        self.specs.push(spec);
        self
    }

    pub fn build<F>(self, link_factory: F) -> PatchPanel
    where
        F: Fn(u32) -> Cat8Link,
    {
        PatchPanel::from_specs(&self.specs, link_factory)
    }
}

impl Default for PatchPanelBuilder {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, Serialize, Default)]
pub struct PatchPanel {
    pub ports: Vec<PatchPort>,
}

impl PatchPanel {
    pub fn from_specs<F>(specs: &[SubsystemSpec], link_factory: F) -> Self
    where
        F: Fn(u32) -> Cat8Link,
    {
        let mut ports = Vec::new();
        for spec in specs {
            for pid in spec.port_ids() {
                ports.push(PatchPort {
                    port_id: pid,
                    subsystem: spec.name.clone(),
                    interface_type: spec.interface_type.clone(),
                    protocol: spec.protocol.clone(),
                    poe_class: spec.poe_class.clone(),
                    link: Some(link_factory(pid)),
                });
            }
        }
        ports.sort_by_key(|p| p.port_id);
        Self { ports }
    }

    /// Build the canonical 12-port base chassis (seeding if empty).
    pub fn default_layout<F>(link_factory: F) -> Self
    where
        F: Fn(u32) -> Cat8Link,
    {
        if registered_subsystems().is_empty() {
            seed_base_registry();
        }
        Self::from_specs(&registered_subsystems(), link_factory)
    }

    pub fn port(&self, port_id: u32) -> Option<&PatchPort> {
        self.ports.iter().find(|p| p.port_id == port_id)
    }

    pub fn subsystems(&self) -> Vec<String> {
        let mut seen = Vec::new();
        for p in &self.ports {
            if !seen.contains(&p.subsystem) {
                seen.push(p.subsystem.clone());
            }
        }
        seen
    }

    pub fn validate(&self) -> Vec<String> {
        let mut issues = Vec::new();
        for p in &self.ports {
            if let Some(link) = &p.link {
                issues.extend(link.validate());
            }
        }
        issues
    }

    pub fn report(&self) -> String {
        self.ports
            .iter()
            .map(|p| p.to_string())
            .collect::<Vec<_>>()
            .join("\n")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_layout_has_12_ports() {
        let panel = PatchPanel::default_layout(|pid| Cat8Link::new(format!("cat8-{pid:02}"), 4.5));
        assert_eq!(panel.ports.len(), 12);
        assert_eq!(
            panel.subsystems(),
            vec![
                "Head & Sensory Node".to_string(),
                "Upper Torso & Kinetic".to_string(),
                "Lower Base & Rig".to_string(),
                "Environmental Matrix".to_string(),
                "External Umbilical".to_string(),
            ]
        );
    }

    #[test]
    fn register_appends_node() {
        clear_registry();
        seed_base_registry();
        register_subsystem(
            SubsystemSpec::new(
                "R&D Lidar Array",
                "Solid-State Lidar + IMU",
                "40GBASE-T",
                Some("PoE++ Type 4 (Up to 90W)"),
                13,
                14,
            )
            .unwrap(),
        )
        .unwrap();
        let panel = PatchPanel::default_layout(|pid| Cat8Link::new(format!("c{pid}"), 3.0));
        assert!(panel.subsystems().contains(&"R&D Lidar Array".to_string()));
        assert_eq!(panel.ports.len(), 14);
        clear_registry();
    }

    #[test]
    fn register_rejects_overlap() {
        clear_registry();
        register_subsystem(
            SubsystemSpec::new(
                "A",
                "iface",
                "40GBASE-T",
                Some("PoE++ Type 4 (90W)"),
                13,
                16,
            )
            .unwrap(),
        )
        .unwrap();
        let res = register_subsystem(
            SubsystemSpec::new(
                "B",
                "iface",
                "40GBASE-T",
                Some("PoE++ Type 4 (90W)"),
                15,
                18,
            )
            .unwrap(),
        );
        assert!(res.is_err());
        clear_registry();
    }

    #[test]
    fn builder_bespoke_layout() {
        let panel = PatchPanelBuilder::new()
            .add_subsystem(
                SubsystemSpec::new("X", "i", "40GBASE-T", Some("PoE++ Type 4 (90W)"), 2, 2)
                    .unwrap(),
            )
            .add_subsystem(SubsystemSpec::new("Y", "i", "40GBASE-T", None, 5, 6).unwrap())
            .build(|pid| Cat8Link::new(format!("c{pid}"), 2.0));
        assert_eq!(
            panel.ports.iter().map(|p| p.port_id).collect::<Vec<_>>(),
            vec![2, 5, 6]
        );
        assert_eq!(panel.subsystems(), vec!["X".to_string(), "Y".to_string()]);
    }
}
