"""Digital-twin emulation of the entire human body and mind.

Extends the surrogate infrastructure (Cat-8 nervous system, patch panel, raw
binary link layer) into a full anatomical + cognitive model. Each body system
and mind module is bound to a port on the surrogate's patch panel and carried
over a Cat-8 link, so the human emulation rides on the same control plane as
the original EDD design.

This is a *structural* digital twin (ontology + state + telemetry + validation
+ raw-binary serialization), not a real-time physiological simulation.
"""

import struct
from dataclasses import dataclass, field
from enum import Enum

from .cat8 import Cat8Link
from .patch_panel import PatchPanel, SubsystemSpec, base_specs
from .raw import PROTO_BIOMETRIC, PROTO_COGNITIVE, PROTO_NATURE, Frame, encode_frame
from .surrogate import Surrogate


class BodySystemId(str, Enum):
    INTEGUMENTARY = "integumentary"
    SKELETAL = "skeletal"
    MUSCULAR = "muscular"
    NERVOUS = "nervous"
    ENDOCRINE = "endocrine"
    CARDIOVASCULAR = "cardiovascular"
    LYMPHATIC = "lymphatic"
    RESPIRATORY = "respiratory"
    DIGESTIVE = "digestive"
    URINARY = "urinary"
    REPRODUCTIVE = "reproductive"


class MindModuleId(str, Enum):
    PERCEPTION = "perception"
    ATTENTION = "attention"
    MEMORY = "memory"
    LEARNING = "learning"
    EMOTION = "emotion"
    EXECUTIVE = "executive"
    LANGUAGE = "language"
    MOTOR = "motor"
    CONSCIOUSNESS = "consciousness"
    SOCIAL = "social"


@dataclass
class Vital:
    """A single biometric reading with a clinically normal range."""

    name: str
    value: float
    unit: str
    low: float
    high: float

    def in_range(self) -> bool:
        return self.low <= self.value <= self.high

    def to_bytes(self) -> bytes:
        return struct.pack("<f", self.value)


@dataclass
class Organ:
    """A component of a body system, bound to a Cat-8 nervous-system link."""

    id: str
    name: str
    system: str
    vitals: list[Vital] = field(default_factory=list)
    port: int | None = None
    link: Cat8Link | None = None
    status: str = "nominal"  # nominal | degraded | failure

    def validate(self) -> list[str]:
        issues: list[str] = []
        for v in self.vitals:
            if not v.in_range():
                issues.append(
                    f"{self.name}/{v.name} out of range: {v.value}{v.unit} "
                    f"(normal {v.low}-{v.high})"
                )
        if self.link is not None:
            issues.extend(self.link.validate())
        if self.status == "failure":
            issues.append(f"{self.name} reported failure")
        return issues

    def telemetry(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "system": self.system,
            "port": self.port,
            "status": self.status,
            "vitals": [
                {
                    "name": v.name,
                    "value": v.value,
                    "unit": v.unit,
                    "in_range": v.in_range(),
                }
                for v in self.vitals
            ],
        }


@dataclass
class BodySystem:
    id: str
    name: str
    organs: list[Organ] = field(default_factory=list)

    def validate(self) -> list[str]:
        issues: list[str] = []
        for o in self.organs:
            issues.extend(o.validate())
        return issues

    def overall_status(self) -> str:
        if any(o.status == "failure" for o in self.organs):
            return "failure"
        if any(not all(v.in_range() for v in o.vitals) for o in self.organs):
            return "degraded"
        return "nominal"


@dataclass
class MindModule:
    """A cognitive function, mapped onto a supporting body system."""

    id: str
    name: str
    activation: float  # 0.0 .. 1.0
    linked_system: str
    port: int | None = None
    link: Cat8Link | None = None
    description: str = ""

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not 0.0 <= self.activation <= 1.0:
            issues.append(
                f"{self.name}: activation {self.activation} out of range 0..1"
            )
        if self.link is not None:
            issues.extend(self.link.validate())
        return issues

    def telemetry(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "activation": self.activation,
            "linked_system": self.linked_system,
            "port": self.port,
        }


@dataclass
class NatureConstruct:
    """A single encoded facet of human nature, bound to a Cat-8 link.

    Human nature — the instinctual and valuative substrate beneath mind — is
    encoded as a normalized weight (0.0..1.0) and rides the *same* artificial
    nervous system as the body and mind. Constructs are grouped (drives,
    temperament, values, moral foundations, higher nature) so the surrogate's
    "character" is inspectable, serializable, and validatable.
    """

    id: str
    name: str
    group: str
    value: float  # 0.0 .. 1.0 encoded weight
    description: str = ""
    port: int | None = None
    link: Cat8Link | None = None

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not 0.0 <= self.value <= 1.0:
            issues.append(f"{self.name}: nature weight {self.value} out of range 0..1")
        if self.link is not None:
            issues.extend(self.link.validate())
        return issues

    def telemetry(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "group": self.group,
            "value": self.value,
            "port": self.port,
        }


@dataclass
class HumanNature:
    """The encoded human nature layer of the digital twin."""

    name: str
    constructs: list[NatureConstruct] = field(default_factory=list)

    def by_group(self, group: str) -> list[NatureConstruct]:
        return [c for c in self.constructs if c.group == group]

    def validate(self) -> list[str]:
        issues: list[str] = []
        for c in self.constructs:
            issues.extend(c.validate())
        return issues

    def is_healthy(self) -> bool:
        return not self.validate()

    def telemetry(self) -> dict:
        return {
            "name": self.name,
            "constructs": len(self.constructs),
            "groups": sorted({c.group for c in self.constructs}),
            "mean_weight": (
                round(sum(c.value for c in self.constructs) / len(self.constructs), 3)
                if self.constructs
                else 0.0
            ),
        }


# The encoded human nature substrate. Each facet is a normalized weight (0..1)
# over five groups. The first group, INSTINCT, is the survival/instinctual
# bedrock — the part of human nature that is encoded directly as the surrogate's
# reflexive substrate — followed by temperament, value orientation, moral
# foundations, and higher-order nature (creativity, meaning, mortality).
_NATURE_BLUEPRINT: list[tuple[str, str, list[tuple[str, str, float, str]]]] = [
    (
        "instinct",
        "Instinct",
        [
            ("fight", "Fight", 0.62, "Confrontational defense response"),
            ("flight", "Flight", 0.70, "Withdrawal from perceived threat"),
            ("freeze", "Freeze", 0.55, "Immobilization under overwhelm"),
            ("seeking", "Seeking", 0.88, "Appetitive exploration drive (Panksepp)"),
            ("attachment", "Attachment", 0.82, "Bonding & proximity maintenance"),
            ("aversion", "Aversion", 0.75, "Withdrawal from noxious stimuli"),
            ("nurturance", "Nurturance", 0.80, "Care-giving toward the vulnerable"),
            ("dominance", "Dominance", 0.58, "Assertion of status / control"),
            ("submission", "Submission", 0.60, "Yielding to higher status"),
            ("play", "Play", 0.66, "Intrinsic, non-instrumental exploration"),
            ("homeostasis", "Homeostasis", 0.90, "Regulation toward equilibrium"),
            ("curiosity", "Curiosity", 0.85, "Information-seeking instinct"),
        ],
    ),
    (
        "temperament",
        "Temperament (Big Five)",
        [
            ("openness", "Openness", 0.82, "Receptivity to novelty & experience"),
            (
                "conscientiousness",
                "Conscientiousness",
                0.75,
                "Order, duty, goal-direction",
            ),
            (
                "extraversion",
                "Extraversion",
                0.60,
                "Orientation to external stimulation",
            ),
            (
                "agreeableness",
                "Agreeableness",
                0.77,
                "Prosocial & cooperative tendency",
            ),
            ("neuroticism", "Neuroticism", 0.35, "Reactivity to negative affect"),
        ],
    ),
    (
        "values",
        "Value Orientation",
        [
            ("self_direction", "Self-Direction", 0.85, "Autonomy of thought & action"),
            ("stimulation", "Stimulation", 0.70, "Novelty, challenge, excitement"),
            ("hedonism", "Hedonism", 0.65, "Pleasure & sensuous gratification"),
            (
                "achievement",
                "Achievement",
                0.78,
                "Personal success per social standards",
            ),
            ("power", "Power", 0.55, "Dominance & control over resources"),
            ("security", "Security", 0.80, "Safety, stability, order of environment"),
            ("conformity", "Conformity", 0.60, "Restraint of impulses per norms"),
            ("tradition", "Tradition", 0.58, "Respect & commitment to customs"),
            ("benevolence", "Benevolence", 0.86, "Welfare of close & in-group others"),
            ("universalism", "Universalism", 0.83, "Welfare of all people & nature"),
        ],
    ),
    (
        "moral",
        "Moral Foundations",
        [
            (
                "care",
                "Care / Harm",
                0.88,
                "Protect from suffering, tend the vulnerable",
            ),
            (
                "fairness",
                "Fairness / Cheating",
                0.84,
                "Proportional justice & reciprocity",
            ),
            (
                "loyalty",
                "Loyalty / Betrayal",
                0.72,
                "Devotion to in-group & allegiance",
            ),
            (
                "authority",
                "Authority / Subversion",
                0.64,
                "Deference to legitimate order",
            ),
            (
                "sanctity",
                "Sanctity / Degradation",
                0.60,
                "Purity, elevation, contamination",
            ),
        ],
    ),
    (
        "higher",
        "Higher Nature",
        [
            (
                "creativity",
                "Creativity",
                0.84,
                "Generative recombination of possibility",
            ),
            (
                "imagination",
                "Imagination",
                0.82,
                "Simulation of absent & counterfactual",
            ),
            ("empathy", "Empathy", 0.87, "Affective & cognitive resonance with others"),
            (
                "narrative_identity",
                "Narrative Identity",
                0.80,
                "Self as an unfolding story",
            ),
            (
                "mortality_awareness",
                "Mortality Awareness",
                0.74,
                "Finitude as meaning-source",
            ),
            ("meaning", "Meaning / Purpose", 0.85, "Coherent aim beyond bare function"),
        ],
    ),
]


# Canonical human blueprint: 11 body systems with representative organs, and
# 10 cognitive modules. Vitals use typical adult reference ranges.
_HUMAN_BLUEPRINT: list[
    tuple[str, str, list[tuple[str, str, list[tuple[str, float, str, float, float]]]]]
] = [
    (
        "integumentary",
        "Integumentary (Skin)",
        [
            (
                "skin",
                "Skin",
                [
                    ("temperature", 36.5, "C", 36.0, 37.5),
                    ("hydration", 70.0, "%", 60.0, 80.0),
                ],
            ),
        ],
    ),
    (
        "skeletal",
        "Skeletal",
        [
            ("skeleton", "Skeleton", [("bmd_tscore", -1.0, "T", -2.5, 1.0)]),
        ],
    ),
    (
        "muscular",
        "Muscular",
        [
            (
                "skeletal_muscle",
                "Skeletal Muscle",
                [("tone", 0.72, "idx", 0.4, 1.0), ("fatigue", 0.12, "idx", 0.0, 0.6)],
            ),
        ],
    ),
    (
        "nervous",
        "Nervous (Cat-8 Core)",
        [
            ("brain", "Brain", [("cortical_activity", 0.82, "idx", 0.4, 1.0)]),
            (
                "spinal_cord",
                "Spinal Cord",
                [("conduction_latency", 5.0, "ms", 2.0, 10.0)],
            ),
        ],
    ),
    (
        "endocrine",
        "Endocrine",
        [
            ("pancreas", "Pancreas", [("insulin", 10.0, "uU/mL", 2.0, 25.0)]),
            ("thyroid", "Thyroid", [("tsh", 2.0, "mIU/L", 0.4, 4.0)]),
        ],
    ),
    (
        "cardiovascular",
        "Cardiovascular",
        [
            (
                "heart",
                "Heart",
                [
                    ("heart_rate", 72.0, "bpm", 60.0, 100.0),
                    ("systolic_bp", 118.0, "mmHg", 90.0, 120.0),
                ],
            ),
            ("vasculature", "Vasculature", [("perfusion", 0.92, "idx", 0.7, 1.0)]),
        ],
    ),
    (
        "lymphatic",
        "Immune / Lymphatic",
        [
            ("immune", "Immune System", [("wbc", 7.0, "10^9/L", 4.0, 11.0)]),
        ],
    ),
    (
        "respiratory",
        "Respiratory",
        [
            (
                "lungs",
                "Lungs",
                [
                    ("resp_rate", 14.0, "/min", 12.0, 20.0),
                    ("spo2", 98.0, "%", 95.0, 100.0),
                ],
            ),
        ],
    ),
    (
        "digestive",
        "Digestive",
        [
            ("stomach", "Stomach", [("ph", 2.0, "pH", 1.5, 3.5)]),
            ("liver", "Liver", [("alt", 25.0, "U/L", 7.0, 56.0)]),
        ],
    ),
    (
        "urinary",
        "Renal / Urinary",
        [
            (
                "kidneys",
                "Kidneys",
                [
                    ("gfr", 95.0, "mL/min", 60.0, 140.0),
                    ("creatinine", 0.9, "mg/dL", 0.6, 1.2),
                ],
            ),
        ],
    ),
    (
        "reproductive",
        "Reproductive",
        [
            ("gonads", "Gonads", [("hormone_index", 1.0, "idx", 0.5, 1.5)]),
        ],
    ),
]

_MIND_BLUEPRINT: list[tuple[str, str, float, str, str]] = [
    ("perception", "Perception", 0.85, "nervous", "Sensory integration"),
    ("attention", "Attention", 0.80, "nervous", "Selective focus"),
    ("memory", "Memory", 0.82, "nervous", "Encoding / recall"),
    ("learning", "Learning", 0.70, "nervous", "Plasticity"),
    ("emotion", "Emotion / Affect", 0.60, "endocrine", "Affective state"),
    ("executive", "Executive Function", 0.83, "nervous", "Planning / inhibition"),
    ("language", "Language", 0.88, "nervous", "Comprehension / speech"),
    ("motor", "Motor Planning", 0.90, "muscular", "Action sequencing"),
    ("consciousness", "Consciousness / Arousal", 0.95, "nervous", "Wakefulness"),
    ("social", "Social Cognition", 0.75, "nervous", "Theory of mind"),
]


@dataclass
class HumanTwin:
    """Digital twin of a full human body, mind, and nature, riding the rig."""

    name: str
    surrogate: Surrogate
    systems: list[BodySystem] = field(default_factory=list)
    mind: list[MindModule] = field(default_factory=list)
    nature: HumanNature = field(default_factory=lambda: HumanNature(""))

    @classmethod
    def factory_default(cls, name: str = "Human-01") -> "HumanTwin":
        surrogate = Surrogate.factory_default(f"{name}-rig")

        specs: list[SubsystemSpec] = list(base_specs())
        next_port = 13  # 1-12 reserved for the canonical surrogate base

        systems: list[BodySystem] = []
        for sys_id, sys_name, organs in _HUMAN_BLUEPRINT:
            start = next_port
            built_organs: list[Organ] = []
            for oid, oname, vitals in organs:
                port = next_port
                next_port += 1
                link = Cat8Link(identifier=f"cat8-{port:02d}", length_m=2.0)
                vobjs = [Vital(n, val, u, lo, hi) for (n, val, u, lo, hi) in vitals]
                built_organs.append(
                    Organ(
                        id=oid,
                        name=oname,
                        system=sys_id,
                        vitals=vobjs,
                        port=port,
                        link=link,
                    )
                )
            end = next_port - 1
            specs.append(
                SubsystemSpec(
                    sys_name,
                    f"{sys_name} telemetry",
                    "40GBASE-T",
                    "PoE++ Type 4 (Up to 90W)",
                    (start, end),
                )
            )
            systems.append(BodySystem(id=sys_id, name=sys_name, organs=built_organs))

        mind_start = next_port
        mind: list[MindModule] = []
        for mid, mname, act, linked, desc in _MIND_BLUEPRINT:
            port = next_port
            next_port += 1
            link = Cat8Link(identifier=f"cat8-{port:02d}", length_m=2.0)
            mind.append(
                MindModule(
                    id=mid,
                    name=mname,
                    activation=act,
                    linked_system=linked,
                    port=port,
                    link=link,
                    description=desc,
                )
            )
        specs.append(
            SubsystemSpec(
                "Cognitive Mesh",
                "Mind / cognitive modules",
                "40GBASE-T",
                "PoE++ Type 4 (Up to 90W)",
                (mind_start, next_port - 1),
            )
        )

        # --- Human Nature layer (ports continue after the cognitive mesh) ---
        nature_start = next_port
        nature: HumanNature = HumanNature(name=f"{name}-nature")
        for _grp_id, grp_name, constructs in _NATURE_BLUEPRINT:
            for cid, cname, val, desc in constructs:
                port = next_port
                next_port += 1
                link = Cat8Link(identifier=f"cat8-{port:02d}", length_m=2.0)
                nature.constructs.append(
                    NatureConstruct(
                        id=cid,
                        name=cname,
                        group=grp_name,
                        value=val,
                        description=desc,
                        port=port,
                        link=link,
                    )
                )
        specs.append(
            SubsystemSpec(
                "Human Nature",
                "Encoded human nature (drives/values/moral/higher)",
                "40GBASE-T",
                "PoE++ Type 4 (Up to 90W)",
                (nature_start, next_port - 1),
            )
        )

        surrogate.patch_panel = PatchPanel.from_specs(
            specs, lambda pid: Cat8Link(identifier=f"cat8-{pid:02d}", length_m=2.0)
        )

        return cls(
            name=name,
            surrogate=surrogate,
            systems=systems,
            mind=mind,
            nature=nature,
        )

    # -- Validation ---------------------------------------------------------
    def validate(self) -> list[str]:
        issues: list[str] = []
        for s in self.systems:
            issues.extend(s.validate())
        for m in self.mind:
            issues.extend(m.validate())
        issues.extend(self.nature.validate())
        issues.extend(self.surrogate.health_check())
        return issues

    def is_healthy(self) -> bool:
        return not self.validate()

    # -- Telemetry -----------------------------------------------------------
    def telemetry(self) -> dict:
        out_of_range = [
            f"{o.name}/{v.name}"
            for s in self.systems
            for o in s.organs
            for v in o.vitals
            if not v.in_range()
        ]
        return {
            "name": self.name,
            "body_systems": len(self.systems),
            "organs": sum(len(s.organs) for s in self.systems),
            "mind_modules": len(self.mind),
            "nature_constructs": len(self.nature.constructs),
            "nature_groups": len(self.nature.telemetry()["groups"]),
            "out_of_range_vitals": out_of_range,
            "overall_status": "nominal" if not out_of_range else "degraded",
            "surrogate_ports": len(self.surrogate.patch_panel.ports),
        }

    # -- Raw binary link layer ----------------------------------------------
    def emit_frames(self) -> list[bytes]:
        """Serialize every organ, mind module, and nature facet into frames."""
        frames: list[bytes] = []
        for s in self.systems:
            for o in s.organs:
                payload = b"".join(v.to_bytes() for v in o.vitals)
                frames.append(
                    encode_frame(
                        Frame(
                            protocol=PROTO_BIOMETRIC,
                            port=o.port or 0,
                            timestamp_us=0,
                            payload=payload,
                        )
                    )
                )
        for m in self.mind:
            payload = struct.pack("<f", m.activation)
            frames.append(
                encode_frame(
                    Frame(
                        protocol=PROTO_COGNITIVE,
                        port=m.port or 0,
                        timestamp_us=0,
                        payload=payload,
                    )
                )
            )
        for c in self.nature.constructs:
            payload = struct.pack("<f", c.value)
            frames.append(
                encode_frame(
                    Frame(
                        protocol=PROTO_NATURE,
                        port=c.port or 0,
                        timestamp_us=0,
                        payload=payload,
                    )
                )
            )
        return frames

    def summary(self) -> str:
        t = self.telemetry()
        lines = [
            f"== Human Digital Twin :: {t['name']} ==",
            f"Body systems : {t['body_systems']}  ({t['organs']} organs)",
            f"Mind modules : {t['mind_modules']}",
            f"Human nature : {t['nature_constructs']} constructs "
            f"across {t['nature_groups']} groups",
            f"Surrogate    : {t['surrogate_ports']} ports on the Cat-8 mesh",
            f"Status       : {t['overall_status']}",
        ]
        if t["out_of_range_vitals"]:
            lines.append("Out of range : " + ", ".join(t["out_of_range_vitals"]))
        return "\n".join(lines)
