from __future__ import annotations

import argparse
import importlib.util
import os
import socket
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "dev" / "resolve_local_ports.py"
FUNCTIONAL_SCRIPT_PATH = ROOT / "scripts" / "dev" / "functional_frontend.sh"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "campaignos_test_resolve_local_ports",
        SCRIPT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load local port resolver")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def reserve_loopback_port(port: int = 0) -> socket.socket:
    reservation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        reservation.bind(("127.0.0.1", port))
    except OSError:
        reservation.close()
        raise
    return reservation


def occupy_default_port(port: int) -> socket.socket | None:
    try:
        return reserve_loopback_port(port)
    except OSError:
        return None


def write_stub(directory: Path, name: str, body: str) -> None:
    target = directory / name
    target.write_text(f"#!/bin/sh\nset -eu\n{body}\n", encoding="utf-8")
    target.chmod(0o755)


def test_parse_assignment_accepts_valid_port() -> None:
    module = load_module()

    assert module.parse_assignment("POSTGRES_PORT=5432") == ("POSTGRES_PORT", 5432)


@pytest.mark.parametrize(
    "value",
    ["missing", "lowercase=5432", "PORT=not-a-number", "PORT=65536", "PORT=-1"],
)
def test_parse_assignment_rejects_invalid_values(value: str) -> None:
    module = load_module()

    with pytest.raises(argparse.ArgumentTypeError):
        module.parse_assignment(value)


def test_resolve_ports_replaces_occupied_port() -> None:
    module = load_module()
    reservation = reserve_loopback_port()
    occupied_port = int(reservation.getsockname()[1])
    try:
        resolved = dict(module.resolve_ports([("POSTGRES_PORT", occupied_port)]))
    finally:
        reservation.close()

    assert resolved["POSTGRES_PORT"] != occupied_port
    assert 1 <= resolved["POSTGRES_PORT"] <= 65535


def test_resolve_ports_returns_unique_ports_for_duplicate_requests() -> None:
    module = load_module()
    reservation = reserve_loopback_port()
    requested_port = int(reservation.getsockname()[1])
    reservation.close()

    resolved = module.resolve_ports(
        [
            ("CAMPAIGNOS_API_PORT", requested_port),
            ("POSTGRES_PORT", requested_port),
            ("CAMPAIGNOS_FRONTEND_PORT", requested_port),
        ]
    )

    ports = [port for _, port in resolved]
    assert ports[0] == requested_port
    assert len(ports) == len(set(ports))


def test_resolve_ports_rejects_duplicate_assignment_names() -> None:
    module = load_module()

    with pytest.raises(ValueError, match="duplicate assignment name"):
        module.resolve_ports([("POSTGRES_PORT", 0), ("POSTGRES_PORT", 0)])


def test_functional_script_propagates_resolved_ports(tmp_path: Path) -> None:
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    trace_file = tmp_path / "trace.log"
    write_stub(
        stub_dir,
        "docker",
        'printf \'docker:%s:postgres=%s:api=%s\\n\' "$*" "$POSTGRES_PORT" '
        '"$CAMPAIGNOS_API_PORT" >> "$TRACE_FILE"',
    )
    write_stub(stub_dir, "curl", "exit 0")
    write_stub(
        stub_dir,
        "make",
        'printf \'make:%s:database=%s\\n\' "$*" "$CAMPAIGNOS_ADMIN_DATABASE_URL" >> "$TRACE_FILE"',
    )
    write_stub(
        stub_dir,
        "npm",
        'printf \'npm:%s:frontend=%s:api=%s\\n\' "$*" "$CAMPAIGNOS_FRONTEND_PORT" '
        '"$CAMPAIGNOS_API_BASE_URL" >> "$TRACE_FILE"',
    )

    reservations = [occupy_default_port(5432), occupy_default_port(3000)]
    env = os.environ.copy()
    env["PATH"] = f"{stub_dir}:{env['PATH']}"
    env["TRACE_FILE"] = str(trace_file)
    env["VIRTUAL_ENV"] = str(tmp_path / "foreign-checkout" / ".venv")
    try:
        result = subprocess.run(  # noqa: S603 - fixed repository script under controlled PATH.
            [str(FUNCTIONAL_SCRIPT_PATH)],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        for reservation in reservations:
            if reservation is not None:
                reservation.close()

    trace = trace_file.read_text(encoding="utf-8")
    assert "[INFO] PostgreSQL port 5432 is occupied; using" in result.stdout
    assert "[INFO] Frontend port 3000 is occupied; using" in result.stdout
    assert "postgres=5432" not in trace
    assert "database=postgresql+psycopg://" in trace
    assert "@127.0.0.1:5432/" not in trace
    assert "--hostname 127.0.0.1 --port" in trace
    assert "frontend=3000" not in trace
    assert "api=http://127.0.0.1:" in trace
    assert "does not match the project environment path" not in result.stderr


def test_functional_script_recovers_transient_buildkit_frontend_disconnect(
    tmp_path: Path,
) -> None:
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    trace_file = tmp_path / "trace.log"
    count_file = tmp_path / "docker-count"
    count_file.write_text("0\n", encoding="utf-8")
    write_stub(
        stub_dir,
        "docker",
        r"""
if [ "$1" = "buildx" ]; then
  printf 'docker:%s\n' "$*" >> "$TRACE_FILE"
  exit 0
fi
count=$(cat "$DOCKER_COUNT_FILE")
next=$((count + 1))
printf '%s\n' "$next" > "$DOCKER_COUNT_FILE"
printf 'docker-attempt:%s:%s\n' "$next" "$*" >> "$TRACE_FILE"
if [ "$count" -eq 0 ]; then
  echo 'target migrate: failed to run Build function: frontend grpc server closed unexpectedly' >&2
  exit 1
fi
""",
    )
    write_stub(stub_dir, "curl", "exit 0")
    write_stub(stub_dir, "make", 'printf \'make:%s\\n\' "$*" >> "$TRACE_FILE"')
    write_stub(stub_dir, "npm", 'printf \'npm:%s\\n\' "$*" >> "$TRACE_FILE"')

    env = os.environ.copy()
    env["PATH"] = f"{stub_dir}:{env['PATH']}"
    env["TRACE_FILE"] = str(trace_file)
    env["DOCKER_COUNT_FILE"] = str(count_file)
    env["VIRTUAL_ENV"] = str(tmp_path / "foreign-checkout" / ".venv")

    result = subprocess.run(  # noqa: S603 - fixed repository script under controlled PATH.
        [str(FUNCTIONAL_SCRIPT_PATH)],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    trace = trace_file.read_text(encoding="utf-8")
    assert count_file.read_text(encoding="utf-8").strip() == "2"
    assert "docker:buildx inspect --bootstrap" in trace
    assert "Docker BuildKit closed its Dockerfile frontend" in result.stderr
    assert "does not match the project environment path" not in result.stderr
    assert "npm:--prefix frontend run dev" in trace


def test_functional_script_does_not_retry_unrelated_build_failure(tmp_path: Path) -> None:
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    trace_file = tmp_path / "trace.log"
    write_stub(
        stub_dir,
        "docker",
        r"""
printf 'docker:%s\n' "$*" >> "$TRACE_FILE"
if [ "$1" = "buildx" ]; then
  exit 99
fi
echo 'Dockerfile parse error: unknown instruction' >&2
exit 7
""",
    )

    env = os.environ.copy()
    env["PATH"] = f"{stub_dir}:{env['PATH']}"
    env["TRACE_FILE"] = str(trace_file)

    result = subprocess.run(  # noqa: S603 - fixed repository script under controlled PATH.
        [str(FUNCTIONAL_SCRIPT_PATH)],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    trace = trace_file.read_text(encoding="utf-8")
    assert result.returncode == 7
    assert trace.count("docker:compose ") == 1
    assert "buildx inspect --bootstrap" not in trace
    assert "Dockerfile parse error: unknown instruction" in result.stdout
