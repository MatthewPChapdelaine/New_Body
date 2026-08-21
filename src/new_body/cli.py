"""Command-line interface for the New Body surrogate control plane."""

import argparse
import sys

from .surrogate import Surrogate
from .telemetry import render_health, render_status


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="new-body",
        description="VR/Physical Surrogate Robot Infrastructure control plane.",
    )
    p.add_argument("--name", default="Surrogate-01", help="surrogate identifier")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="print full infrastructure status")
    sub.add_parser("health", help="run link/power/ESD health check")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    surrogate = Surrogate.factory_default(args.name)

    if args.command == "status":
        print(render_status(surrogate))
    elif args.command == "health":
        print(render_health(surrogate))
        return 0 if surrogate.is_healthy() else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
