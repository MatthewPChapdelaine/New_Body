"""Command-line interface for the New Body surrogate control plane."""

import argparse
import sys

from .body import HumanTwin
from .raw import (
    PROTO_SENSORY,
    Frame,
    decode_frame,
    encode_frame,
)
from .surrogate import Surrogate
from .telemetry import render_health, render_status
from .visualize import write_explorer


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="new-body",
        description="VR/Physical Surrogate Robot Infrastructure control plane.",
    )
    p.add_argument("--name", default="Surrogate-01", help="surrogate identifier")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="print full infrastructure status")
    sub.add_parser("health", help="run link/power/ESD health check")
    sub.add_parser("frame", help="encode + decode a sample raw binary frame")
    sub.add_parser(
        "human",
        help="emulate the full human body, mind & nature (digital twin)",
    )

    explore_p = sub.add_parser(
        "explore", help="generate an interactive HTML explorer from the live model"
    )
    explore_p.add_argument(
        "--out",
        default="new_body_explorer.html",
        help="output HTML path (default: new_body_explorer.html)",
    )
    explore_p.add_argument(
        "--no-twin",
        action="store_true",
        help="omit the human body & mind digital twin section",
    )
    return p


def _demo_frame() -> None:
    frame = Frame(
        protocol=PROTO_SENSORY,
        port=3,
        timestamp_us=1_234_567,
        payload=bytes([0xDE, 0xAD, 0xBE, 0xEF]),
    )
    raw = encode_frame(frame)
    print(f"encoded ({len(raw)} bytes): {raw.hex()}")
    decoded = decode_frame(raw)
    print(
        f"decoded: proto={decoded.protocol} port={decoded.port} "
        f"ts={decoded.timestamp_us} payload={decoded.payload.hex()}"
    )


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    surrogate = Surrogate.factory_default(args.name)

    if args.command == "status":
        print(render_status(surrogate))
    elif args.command == "health":
        print(render_health(surrogate))
        return 0 if surrogate.is_healthy() else 1
    elif args.command == "frame":
        _demo_frame()
    elif args.command == "human":
        _demo_human(args.name)
    elif args.command == "explore":
        surrogate = Surrogate.factory_default(args.name)
        twin = None if args.no_twin else HumanTwin.factory_default(f"{args.name}-twin")
        out = write_explorer(args.out, surrogate, twin)
        print(f"wrote interactive explorer -> {out}")
    return 0


def _demo_human(name: str) -> None:
    twin = HumanTwin.factory_default(name)
    print(twin.summary())
    print()
    frames = twin.emit_frames()
    print(
        f"Emitted {len(frames)} raw Cat-8 frames carrying body + mind + "
        f"human-nature telemetry ({len(twin.nature.constructs)} nature facets)"
    )
    if frames:
        print(f"sample frame: {frames[0].hex()}")


if __name__ == "__main__":
    sys.exit(main())
