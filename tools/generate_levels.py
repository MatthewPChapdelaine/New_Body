"""Generate the 100-level progression table for the New Body R&D Contributor Game.

Emits two artifacts consumed by the HTML5 client:
  - game/levels.json   machine-readable progression data
  - game/levels.js     same data as `window.LEVELS = [...]` (avoids file:// CORS)

Leveling model
--------------
Per-level XP cost rises gently so early contributions feel rewarding while the
top of the ladder stays aspirational:

    cost(L -> L+1) = BASE + STEP * (L - 1)        # L = current level
    cum_xp(L)      = 100*(L-1) + 10*(L-1)*(L-2)   # XP needed to *reach* L

Rewards
-------
  * Every level grants a cosmetic "research badge" (tier + level frame).
  * Privilege unlocks at key levels open real repo capabilities.
  * Physical / digital prizes land on milestone levels (10/25/50/75/100).
"""

from __future__ import annotations

import json
from pathlib import Path

BASE = 100
STEP = 20

TIERS = [
    (1, 10, "Initiate Researcher", "Bronze"),
    (11, 20, "Lab Technician", "Silver"),
    (21, 30, "Associate Engineer", "Silver II"),
    (31, 40, "R&D Specialist", "Gold"),
    (41, 50, "Senior Contributor", "Gold II"),
    (51, 60, "Principal Innovator", "Platinum"),
    (61, 70, "Research Lead", "Platinum II"),
    (71, 80, "Distinguished Architect", "Diamond"),
    (81, 90, "Fellow of the Body", "Diamond II"),
    (91, 100, "Chief Surrogate Architect", "Legend"),
]

PRIVILEGES = {
    20: "Label & assign issues",
    40: "Join the triage team",
    60: "Write access to examples/",
    80: "Merge rights on docs/",
    100: "Architect seat (roadmap vote)",
}

PRIZES = {
    10: ("Digital", "Animated contributor badge + README hall-of-fame entry"),
    25: ("Physical", "New Body enamel pin + sticker pack"),
    50: ("Physical", "Embroidered lab hoodie"),
    75: ("Physical", "Mechanical keyboard + Cat-8 dev kit"),
    100: ("Legend", "Name etched on the chassis plaque + rig build tour"),
}

MILESTONES = set(PRIZES.keys())


def cum_xp(level: int) -> int:
    """Total XP required to *reach* `level` (level 1 == 0 XP)."""
    if level <= 1:
        return 0
    n = level - 1
    return BASE * n + 10 * n * (n - 1)


def tier_for(level: int) -> tuple[str, str]:
    for lo, hi, name, rank in TIERS:
        if lo <= level <= hi:
            return name, rank
    raise ValueError(level)


def build_levels() -> list[dict]:
    levels: list[dict] = []
    for lvl in range(1, 101):
        tier_name, rank = tier_for(lvl)
        entry: dict = {
            "level": lvl,
            "tier": tier_name,
            "rank": rank,
            "xp_to_reach": cum_xp(lvl),
            "xp_for_next": cum_xp(lvl + 1) - cum_xp(lvl) if lvl < 100 else 0,
            "reward": {
                "type": "badge",
                "name": f"{tier_name} — Level {lvl} badge",
            },
        }
        if lvl in PRIVILEGES:
            entry["reward"] = {
                "type": "privilege",
                "name": PRIVILEGES[lvl],
            }
        if lvl in PRIZES:
            kind, name = PRIZES[lvl]
            entry["reward"] = {"type": "prize", "kind": kind, "name": name}
            entry["milestone"] = True
        levels.append(entry)
    return levels


def main() -> None:
    levels = build_levels()
    out_dir = Path(__file__).resolve().parent.parent / "game"
    out_dir.mkdir(exist_ok=True)

    (out_dir / "levels.json").write_text(json.dumps(levels, indent=2) + "\n")
    (out_dir / "levels.js").write_text(
        "window.LEVELS = " + json.dumps(levels, indent=2) + ";\n"
    )
    print(f"wrote {len(levels)} levels to {out_dir}/levels.json and levels.js")
    print("top of ladder:", cum_xp(100), "XP to reach level 100")


if __name__ == "__main__":
    main()
