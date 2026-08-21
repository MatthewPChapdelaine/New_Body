"""Telemetry + diagnostics rendering for the surrogate control plane."""

from .surrogate import Surrogate


def render_status(s: Surrogate) -> str:
    t = s.telemetry()
    lines = [
        f"== New Body :: {t['name']} ==",
        f"Core Platform : {t['core_platform']}",
        f"VR Integration: {t['vr_integration']}",
        f"Patch Panel   : {t['ports']} ports / {len(t['subsystems'])} subsystems",
        f"PoE Draw      : {t['total_poe_watts']:.0f}W aggregate across "
        f"{len(s.poe)} independent {t['poe_ceiling_watts']:.0f}W lines",
        "",
        "-- Patch Panel Layout --",
        s.patch_panel.report(),
        "",
        "-- PoE++ Delivery Path --",
    ]
    for subsystem, delivery in s.poe.items():
        lines.append(f"[{subsystem}]")
        lines.append(delivery.diagram())
        lines.append("")
    return "\n".join(lines)


def render_health(s: Surrogate) -> str:
    issues = s.health_check()
    if not issues:
        return f"[OK] {s.name} nominal - all links, power, and ESD validated."
    return "[WARN] " + "; ".join(issues)
