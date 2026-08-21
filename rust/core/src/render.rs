//! Status + health rendering for the surrogate control plane.

use crate::surrogate::Surrogate;

pub fn render_status(s: &Surrogate) -> String {
    let t = s.telemetry();
    let mut out = vec![
        format!("== New Body :: {} ==", t.name),
        format!("Core Platform : {}", t.core_platform),
        format!("VR Integration: {}", t.vr_integration),
        format!(
            "Patch Panel   : {} ports / {} subsystems",
            t.ports,
            t.subsystems.len()
        ),
        format!(
            "PoE Draw      : {:.0}W aggregate across {} independent {:.0}W lines",
            t.total_poe_watts,
            s.poe.len(),
            t.poe_ceiling_watts
        ),
        String::new(),
        "-- Patch Panel Layout --".to_string(),
        s.patch_panel.report(),
        String::new(),
        "-- PoE++ Delivery Path --".to_string(),
    ];
    for (subsystem, delivery) in &s.poe {
        out.push(format!("[{subsystem}]"));
        out.push(delivery.diagram());
        out.push(String::new());
    }
    out.join("\n")
}

pub fn render_health(s: &Surrogate) -> String {
    let issues = s.health_check();
    if issues.is_empty() {
        format!(
            "[OK] {} nominal - all links, power, and ESD validated.",
            s.name
        )
    } else {
        format!("[WARN] {}", issues.join("; "))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn status_renders_panel() {
        let s = Surrogate::factory_default("S");
        let out = render_status(&s);
        assert!(out.contains("== New Body :: S =="));
        assert!(out.contains("Port 01 | Head & Sensory Node"));
    }

    #[test]
    fn health_renders_ok() {
        let s = Surrogate::factory_default("S");
        assert!(render_health(&s).starts_with("[OK]"));
    }
}
