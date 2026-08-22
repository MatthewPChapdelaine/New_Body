//! Digital-twin emulation of the entire human body and mind.
//!
//! Extends the surrogate infrastructure (Cat-8 nervous system, patch panel,
//! raw binary link layer) into a full anatomical + cognitive model. Each body
//! system and mind module is bound to a Cat-8 link, so the human emulation
//! rides on the same control plane as the EDD design. This is a *structural*
//! digital twin (ontology + state + telemetry + validation + raw-binary
//! serialization), not a real-time physiological simulation.

use serde::Serialize;

use crate::cat8::Cat8Link;
use crate::patch_panel::{base_specs, PatchPanel, SubsystemSpec};
use crate::raw::{Frame, PROTO_BIOMETRIC, PROTO_COGNITIVE};
use crate::surrogate::Surrogate;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BodySystemId {
    Integumentary,
    Skeletal,
    Muscular,
    Nervous,
    Endocrine,
    Cardiovascular,
    Lymphatic,
    Respiratory,
    Digestive,
    Urinary,
    Reproductive,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MindModuleId {
    Perception,
    Attention,
    Memory,
    Learning,
    Emotion,
    Executive,
    Language,
    Motor,
    Consciousness,
    Social,
}

#[derive(Debug, Clone, Serialize)]
pub struct Vital {
    pub name: String,
    pub value: f32,
    pub unit: String,
    pub low: f32,
    pub high: f32,
}

impl Vital {
    pub fn in_range(&self) -> bool {
        self.value >= self.low && self.value <= self.high
    }

    pub fn to_bytes(&self) -> [u8; 4] {
        self.value.to_le_bytes()
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct Organ {
    pub id: String,
    pub name: String,
    pub system: BodySystemId,
    pub vitals: Vec<Vital>,
    pub port: Option<u32>,
    pub link: Option<Cat8Link>,
    pub status: String,
}

impl Organ {
    pub fn validate(&self) -> Vec<String> {
        let mut issues = Vec::new();
        for v in &self.vitals {
            if !v.in_range() {
                issues.push(format!(
                    "{}: vital {} out of range: {} {} (normal {}-{})",
                    self.name, v.name, v.value, v.unit, v.low, v.high
                ));
            }
        }
        if let Some(link) = &self.link {
            issues.extend(link.validate());
        }
        if self.status == "failure" {
            issues.push(format!("{} reported failure", self.name));
        }
        issues
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct BodySystem {
    pub id: BodySystemId,
    pub name: String,
    pub organs: Vec<Organ>,
}

impl BodySystem {
    pub fn validate(&self) -> Vec<String> {
        let mut issues = Vec::new();
        for o in &self.organs {
            issues.extend(o.validate());
        }
        issues
    }

    pub fn overall_status(&self) -> &'static str {
        if self.organs.iter().any(|o| o.status == "failure") {
            "failure"
        } else if self
            .organs
            .iter()
            .any(|o| !o.vitals.iter().all(Vital::in_range))
        {
            "degraded"
        } else {
            "nominal"
        }
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct MindModule {
    pub id: MindModuleId,
    pub name: String,
    pub activation: f32,
    pub linked_system: BodySystemId,
    pub port: Option<u32>,
    pub link: Option<Cat8Link>,
    pub description: String,
}

impl MindModule {
    pub fn validate(&self) -> Vec<String> {
        let mut issues = Vec::new();
        if !(0.0..=1.0).contains(&self.activation) {
            issues.push(format!(
                "{}: activation {} out of range 0..1",
                self.name, self.activation
            ));
        }
        if let Some(link) = &self.link {
            issues.extend(link.validate());
        }
        issues
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct HumanTwin {
    pub name: String,
    pub surrogate: Surrogate,
    pub systems: Vec<BodySystem>,
    pub mind: Vec<MindModule>,
}

impl HumanTwin {
    pub fn factory_default(name: &str) -> HumanTwin {
        let mut surrogate = Surrogate::factory_default(&format!("{name}-rig"));

        let mut specs = base_specs();
        let mut next_port: u32 = 13; // 1-12 reserved for the canonical base

        let mut systems: Vec<BodySystem> = Vec::new();
        for (sys_id, sys_name, organs) in human_blueprint() {
            let start = next_port;
            let mut built = Vec::new();
            for (oid, oname, vitals) in organs {
                let port = next_port;
                next_port += 1;
                let link = Cat8Link::new(format!("cat8-{port:02}"), 2.0);
                let vobjs: Vec<Vital> = vitals
                    .iter()
                    .map(|(n, val, u, lo, hi)| Vital {
                        name: n.to_string(),
                        value: *val,
                        unit: u.to_string(),
                        low: *lo,
                        high: *hi,
                    })
                    .collect();
                built.push(Organ {
                    id: oid.to_string(),
                    name: oname.to_string(),
                    system: sys_id,
                    vitals: vobjs,
                    port: Some(port),
                    link: Some(link),
                    status: "nominal".into(),
                });
            }
            let end = next_port - 1;
            specs.push(
                SubsystemSpec::new(
                    sys_name,
                    &format!("{sys_name} telemetry"),
                    "40GBASE-T",
                    Some("PoE++ Type 4 (Up to 90W)"),
                    start,
                    end,
                )
                .unwrap(),
            );
            systems.push(BodySystem {
                id: sys_id,
                name: sys_name.to_string(),
                organs: built,
            });
        }

        let mind_start = next_port;
        let mut mind: Vec<MindModule> = Vec::new();
        for (mid, mname, act, linked, desc) in mind_blueprint() {
            let port = next_port;
            next_port += 1;
            let link = Cat8Link::new(format!("cat8-{port:02}"), 2.0);
            mind.push(MindModule {
                id: mid,
                name: mname.to_string(),
                activation: act,
                linked_system: linked,
                port: Some(port),
                link: Some(link),
                description: desc.to_string(),
            });
        }
        specs.push(
            SubsystemSpec::new(
                "Cognitive Mesh",
                "Mind / cognitive modules",
                "40GBASE-T",
                Some("PoE++ Type 4 (Up to 90W)"),
                mind_start,
                next_port - 1,
            )
            .unwrap(),
        );

        surrogate.patch_panel =
            PatchPanel::from_specs(&specs, |pid| Cat8Link::new(format!("cat8-{pid:02}"), 2.0));

        HumanTwin {
            name: name.to_string(),
            surrogate,
            systems,
            mind,
        }
    }

    pub fn validate(&self) -> Vec<String> {
        let mut issues = Vec::new();
        for s in &self.systems {
            issues.extend(s.validate());
        }
        for m in &self.mind {
            issues.extend(m.validate());
        }
        issues.extend(self.surrogate.health_check());
        issues
    }

    pub fn is_healthy(&self) -> bool {
        self.validate().is_empty()
    }

    pub fn emit_frames(&self) -> Vec<Vec<u8>> {
        let mut frames = Vec::new();
        for s in &self.systems {
            for o in &s.organs {
                let mut payload = Vec::new();
                for v in &o.vitals {
                    payload.extend_from_slice(&v.to_bytes());
                }
                frames.push(
                    Frame {
                        protocol: PROTO_BIOMETRIC,
                        port: o.port.unwrap_or(0) as u16,
                        timestamp_us: 0,
                        payload,
                    }
                    .encode(),
                );
            }
        }
        for m in &self.mind {
            frames.push(
                Frame {
                    protocol: PROTO_COGNITIVE,
                    port: m.port.unwrap_or(0) as u16,
                    timestamp_us: 0,
                    payload: m.activation.to_le_bytes().to_vec(),
                }
                .encode(),
            );
        }
        frames
    }

    pub fn summary(&self) -> String {
        let organs: usize = self.systems.iter().map(|s| s.organs.len()).sum();
        let out_of_range: usize = self
            .systems
            .iter()
            .flat_map(|s| s.organs.iter())
            .flat_map(|o| o.vitals.iter())
            .filter(|v| !v.in_range())
            .count();
        let status = if out_of_range == 0 {
            "nominal"
        } else {
            "degraded"
        };
        format!(
            "== Human Digital Twin :: {} ==\n\
             Body systems : {}  ({} organs)\n\
             Mind modules : {}\n\
             Surrogate    : {} ports on the Cat-8 mesh\n\
             Status       : {}",
            self.name,
            self.systems.len(),
            organs,
            self.mind.len(),
            self.surrogate.patch_panel.ports.len(),
            status
        )
    }
}

type VitalSpec = (&'static str, f32, &'static str, f32, f32);
type OrganSpec = (&'static str, &'static str, Vec<VitalSpec>);
type SystemSpec = (BodySystemId, &'static str, Vec<OrganSpec>);

fn human_blueprint() -> Vec<SystemSpec> {
    vec![
        (
            BodySystemId::Integumentary,
            "Integumentary (Skin)",
            vec![(
                "skin",
                "Skin",
                vec![
                    ("temperature", 36.5, "C", 36.0, 37.5),
                    ("hydration", 70.0, "%", 60.0, 80.0),
                ],
            )],
        ),
        (
            BodySystemId::Skeletal,
            "Skeletal",
            vec![(
                "skeleton",
                "Skeleton",
                vec![("bmd_tscore", -1.0, "T", -2.5, 1.0)],
            )],
        ),
        (
            BodySystemId::Muscular,
            "Muscular",
            vec![(
                "skeletal_muscle",
                "Skeletal Muscle",
                vec![
                    ("tone", 0.72, "idx", 0.4, 1.0),
                    ("fatigue", 0.12, "idx", 0.0, 0.6),
                ],
            )],
        ),
        (
            BodySystemId::Nervous,
            "Nervous (Cat-8 Core)",
            vec![
                (
                    "brain",
                    "Brain",
                    vec![("cortical_activity", 0.82, "idx", 0.4, 1.0)],
                ),
                (
                    "spinal_cord",
                    "Spinal Cord",
                    vec![("conduction_latency", 5.0, "ms", 2.0, 10.0)],
                ),
            ],
        ),
        (
            BodySystemId::Endocrine,
            "Endocrine",
            vec![
                (
                    "pancreas",
                    "Pancreas",
                    vec![("insulin", 10.0, "uU/mL", 2.0, 25.0)],
                ),
                ("thyroid", "Thyroid", vec![("tsh", 2.0, "mIU/L", 0.4, 4.0)]),
            ],
        ),
        (
            BodySystemId::Cardiovascular,
            "Cardiovascular",
            vec![
                (
                    "heart",
                    "Heart",
                    vec![
                        ("heart_rate", 72.0, "bpm", 60.0, 100.0),
                        ("systolic_bp", 118.0, "mmHg", 90.0, 120.0),
                    ],
                ),
                (
                    "vasculature",
                    "Vasculature",
                    vec![("perfusion", 0.92, "idx", 0.7, 1.0)],
                ),
            ],
        ),
        (
            BodySystemId::Lymphatic,
            "Immune / Lymphatic",
            vec![(
                "immune",
                "Immune System",
                vec![("wbc", 7.0, "10^9/L", 4.0, 11.0)],
            )],
        ),
        (
            BodySystemId::Respiratory,
            "Respiratory",
            vec![(
                "lungs",
                "Lungs",
                vec![
                    ("resp_rate", 14.0, "/min", 12.0, 20.0),
                    ("spo2", 98.0, "%", 95.0, 100.0),
                ],
            )],
        ),
        (
            BodySystemId::Digestive,
            "Digestive",
            vec![
                ("stomach", "Stomach", vec![("ph", 2.0, "pH", 1.5, 3.5)]),
                ("liver", "Liver", vec![("alt", 25.0, "U/L", 7.0, 56.0)]),
            ],
        ),
        (
            BodySystemId::Urinary,
            "Renal / Urinary",
            vec![(
                "kidneys",
                "Kidneys",
                vec![
                    ("gfr", 95.0, "mL/min", 60.0, 140.0),
                    ("creatinine", 0.9, "mg/dL", 0.6, 1.2),
                ],
            )],
        ),
        (
            BodySystemId::Reproductive,
            "Reproductive",
            vec![(
                "gonads",
                "Gonads",
                vec![("hormone_index", 1.0, "idx", 0.5, 1.5)],
            )],
        ),
    ]
}

type MindSpec = (MindModuleId, &'static str, f32, BodySystemId, &'static str);

fn mind_blueprint() -> Vec<MindSpec> {
    vec![
        (
            MindModuleId::Perception,
            "Perception",
            0.85,
            BodySystemId::Nervous,
            "Sensory integration",
        ),
        (
            MindModuleId::Attention,
            "Attention",
            0.80,
            BodySystemId::Nervous,
            "Selective focus",
        ),
        (
            MindModuleId::Memory,
            "Memory",
            0.82,
            BodySystemId::Nervous,
            "Encoding / recall",
        ),
        (
            MindModuleId::Learning,
            "Learning",
            0.70,
            BodySystemId::Nervous,
            "Plasticity",
        ),
        (
            MindModuleId::Emotion,
            "Emotion / Affect",
            0.60,
            BodySystemId::Endocrine,
            "Affective state",
        ),
        (
            MindModuleId::Executive,
            "Executive Function",
            0.83,
            BodySystemId::Nervous,
            "Planning / inhibition",
        ),
        (
            MindModuleId::Language,
            "Language",
            0.88,
            BodySystemId::Nervous,
            "Comprehension / speech",
        ),
        (
            MindModuleId::Motor,
            "Motor Planning",
            0.90,
            BodySystemId::Muscular,
            "Action sequencing",
        ),
        (
            MindModuleId::Consciousness,
            "Consciousness / Arousal",
            0.95,
            BodySystemId::Nervous,
            "Wakefulness",
        ),
        (
            MindModuleId::Social,
            "Social Cognition",
            0.75,
            BodySystemId::Nervous,
            "Theory of mind",
        ),
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn factory_default_full_body_and_mind() {
        let twin = HumanTwin::factory_default("Human-QA");
        assert_eq!(twin.systems.len(), 11);
        assert_eq!(twin.mind.len(), 10);
        assert!(twin.systems.iter().any(|s| s.id == BodySystemId::Nervous));
        assert!(twin.mind.iter().any(|m| m.id == MindModuleId::Language));
    }

    #[test]
    fn canonical_twin_is_healthy() {
        let twin = HumanTwin::factory_default("Human-01");
        assert!(twin.is_healthy());
        assert!(twin.surrogate.patch_panel.ports.len() > 12);
    }

    #[test]
    fn emit_frames_roundtrip() {
        let twin = HumanTwin::factory_default("Human-01");
        let frames = twin.emit_frames();
        let organs: usize = twin.systems.iter().map(|s| s.organs.len()).sum();
        assert_eq!(frames.len(), organs + twin.mind.len());

        let decoded = Frame::decode(&frames[0]).unwrap();
        assert_eq!(decoded.protocol, PROTO_BIOMETRIC);
        assert_eq!(decoded.payload.len() % 4, 0);

        let cog = twin
            .emit_frames()
            .iter()
            .map(|f| Frame::decode(f).unwrap())
            .find(|f| f.protocol == PROTO_COGNITIVE)
            .unwrap();
        let act = f32::from_le_bytes(cog.payload.clone().try_into().unwrap());
        assert!((0.0..=1.0).contains(&act));
    }

    #[test]
    fn out_of_range_detected() {
        let mut twin = HumanTwin::factory_default("Human-01");
        twin.systems[0].organs[0].vitals[0].value = 999.0;
        assert!(!twin.validate().is_empty());
        assert!(!twin.is_healthy());
    }
}
