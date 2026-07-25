#!/usr/bin/env python3
"""Resolve loopback TCP ports for local CampaignOS services.

Requested ports are preserved when available. Occupied or duplicate ports are
replaced with ephemeral loopback ports. All sockets remain reserved until the
complete set has been selected so the returned ports are unique within one run.
"""

from __future__ import annotations

import argparse
import re
import socket
from collections.abc import Iterable

_LOOPBACK = "127.0.0.1"
_ASSIGNMENT_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


def parse_assignment(value: str) -> tuple[str, int]:
    """Parse and validate a NAME=PORT assignment."""
    name, separator, raw_port = value.partition("=")
    if not separator or not _ASSIGNMENT_PATTERN.fullmatch(name):
        raise argparse.ArgumentTypeError(f"invalid port assignment: {value!r}")
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid TCP port: {raw_port!r}") from exc
    if not 0 <= port <= 65535:
        raise argparse.ArgumentTypeError(f"TCP port out of range: {port}")
    return name, port


def resolve_ports(assignments: Iterable[tuple[str, int]]) -> list[tuple[str, int]]:
    """Resolve requested ports while preventing duplicates within the returned set."""
    reservations: list[socket.socket] = []
    resolved: list[tuple[str, int]] = []
    seen_names: set[str] = set()
    try:
        for name, requested_port in assignments:
            if name in seen_names:
                raise ValueError(f"duplicate assignment name: {name}")
            seen_names.add(name)

            reservation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                reservation.bind((_LOOPBACK, requested_port))
            except OSError:
                reservation.close()
                reservation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                reservation.bind((_LOOPBACK, 0))

            reservations.append(reservation)
            resolved.append((name, int(reservation.getsockname()[1])))
        return resolved
    finally:
        for reservation in reservations:
            reservation.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preserve available loopback ports and replace occupied ports safely."
    )
    parser.add_argument("assignments", nargs="+", type=parse_assignment, metavar="NAME=PORT")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        resolved = resolve_ports(args.assignments)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    for name, port in resolved:
        print(f"{name}={port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
