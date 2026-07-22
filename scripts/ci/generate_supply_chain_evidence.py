#!/usr/bin/env python3
"""Generate deterministic SBOM, source manifest and unsigned SLSA provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _git(root: Path, *args: str) -> str:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git is required to generate source evidence")
    result = subprocess.run(  # noqa: S603 - absolute git path; shell is never used.
        [git, "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _timestamp(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, tz=UTC).isoformat().replace("+00:00", "Z")


def _python_components(root: Path) -> list[dict[str, object]]:
    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    components: list[dict[str, object]] = []
    for package in lock.get("package", []):
        name = str(package["name"])
        version = str(package["version"])
        hashes: set[str] = set()
        sdist = package.get("sdist")
        if isinstance(sdist, dict) and str(sdist.get("hash", "")).startswith("sha256:"):
            hashes.add(str(sdist["hash"]).removeprefix("sha256:"))
        for wheel in package.get("wheels", []):
            value = str(wheel.get("hash", ""))
            if value.startswith("sha256:"):
                hashes.add(value.removeprefix("sha256:"))
        component: dict[str, object] = {
            "type": "library",
            "bom-ref": f"pkg:pypi/{quote(name, safe='-._~')}@{quote(version, safe='-._~')}",
            "name": name,
            "version": version,
            "purl": f"pkg:pypi/{quote(name, safe='-._~')}@{quote(version, safe='-._~')}",
            "properties": [{"name": "campaignos:ecosystem", "value": "python"}],
        }
        if hashes:
            component["hashes"] = [{"alg": "SHA-256", "content": value} for value in sorted(hashes)]
        components.append(component)
    return sorted(components, key=lambda item: str(item["bom-ref"]))


def _npm_name(package_path: str, package: dict[str, Any]) -> str:
    if package.get("name"):
        return str(package["name"])
    marker = "node_modules/"
    if marker not in package_path:
        return package_path or "campaignos-frontend"
    return package_path.rsplit(marker, 1)[1]


def _npm_components(root: Path) -> list[dict[str, object]]:
    lock = json.loads((root / "frontend/package-lock.json").read_text(encoding="utf-8"))
    components: list[dict[str, object]] = []
    for package_path, raw in lock.get("packages", {}).items():
        if not package_path or not raw.get("version"):
            continue
        name = _npm_name(package_path, raw)
        version = str(raw["version"])
        encoded_name = quote(name, safe="-._~")
        component: dict[str, object] = {
            "type": "library",
            "bom-ref": f"pkg:npm/{encoded_name}@{quote(version, safe='-._~')}",
            "name": name,
            "version": version,
            "purl": f"pkg:npm/{encoded_name}@{quote(version, safe='-._~')}",
            "properties": [{"name": "campaignos:ecosystem", "value": "npm"}],
        }
        if raw.get("integrity"):
            component["properties"].append(
                {"name": "campaignos:npm-integrity", "value": str(raw["integrity"])}
            )
        components.append(component)
    return sorted(components, key=lambda item: str(item["bom-ref"]))


def _source_manifest(root: Path, revision: str, generated_at: str) -> dict[str, object]:
    tracked = _git(root, "ls-files", "-z").split("\0")
    files: list[dict[str, object]] = []
    for relative in sorted(item for item in tracked if item):
        path = root / relative
        if not path.is_file():
            continue
        data = path.read_bytes()
        files.append({"path": relative, "sha256": _sha256(data), "size": len(data)})
    return {
        "schema_version": 1,
        "revision": revision,
        "generated_at": generated_at,
        "files": files,
    }


def _material(root: Path, relative: str) -> dict[str, object]:
    data = (root / relative).read_bytes()
    return {"uri": relative, "digest": {"sha256": _sha256(data)}}


def generate(root: Path, output: Path, *, repository: str, revision: str, epoch: int) -> None:
    output.mkdir(parents=True, exist_ok=True)
    generated_at = _timestamp(epoch)
    components = _python_components(root) + _npm_components(root)
    components.sort(key=lambda item: str(item["bom-ref"]))
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {
            "timestamp": generated_at,
            "component": {
                "type": "application",
                "bom-ref": f"git+{repository}@{revision}",
                "name": "campaignos",
                "version": revision,
                "properties": [{"name": "campaignos:production-status", "value": "BLOCKED"}],
            },
        },
        "components": components,
    }
    _write_json(output / "cyclonedx-sbom.json", sbom)

    manifest = _source_manifest(root, revision, generated_at)
    _write_json(output / "source-manifest.json", manifest)
    manifest_digest = _sha256((output / "source-manifest.json").read_bytes())
    materials = [
        _material(root, relative)
        for relative in (
            "uv.lock",
            "frontend/package-lock.json",
            ".github/workflows/campaignos-ci.yml",
            ".github/campaignos-security-policy.json",
            "backend/Dockerfile",
            "frontend/Dockerfile",
        )
    ]
    provenance = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {
                "name": "source-manifest.json",
                "digest": {"sha256": manifest_digest},
            }
        ],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "https://campaignos.example/supply-chain-evidence/v1",
                "externalParameters": {
                    "repository": repository,
                    "revision": revision,
                    "production_status": "BLOCKED",
                },
                "internalParameters": {"generator": "scripts/ci/generate_supply_chain_evidence.py"},
                "resolvedDependencies": materials,
            },
            "runDetails": {
                "builder": {"id": "https://github.com/BernydotJar/OS-Electoral/actions"},
                "metadata": {
                    "invocationId": revision,
                    "startedOn": generated_at,
                    "finishedOn": generated_at,
                },
                "byproducts": [
                    {"name": "cyclonedx-sbom.json"},
                    {"name": "source-manifest.json"},
                ],
            },
        },
    }
    _write_json(output / "provenance.intoto.json", provenance)
    report = {
        "schema_version": 1,
        "revision": revision,
        "generated_at": generated_at,
        "sbom_format": "CycloneDX 1.6",
        "provenance_format": "in-toto Statement v1 / SLSA Provenance v1",
        "embedded_signature_status": "UNSIGNED",
        "github_keyless_attestation": "REQUESTED_BY_CAMPAIGNOS_CI",
        "signature_claim": False,
        "production_status": "BLOCKED",
    }
    _write_json(output / "evidence-report.json", report)

    checksum_paths = sorted(
        path for path in output.iterdir() if path.is_file() and path.name != "SHA256SUMS"
    )
    lines = [f"{_sha256(path.read_bytes())}  {path.name}" for path in checksum_paths]
    (output / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--repository",
        default=os.getenv("GITHUB_SERVER_URL", "https://github.com")
        + "/"
        + os.getenv("GITHUB_REPOSITORY", "BernydotJar/OS-Electoral"),
    )
    parser.add_argument("--revision")
    parser.add_argument("--source-date-epoch", type=int)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    revision = args.revision or os.getenv("GITHUB_SHA") or _git(root, "rev-parse", "HEAD")
    epoch = args.source_date_epoch
    if epoch is None:
        epoch = int(
            os.getenv("SOURCE_DATE_EPOCH") or _git(root, "show", "-s", "--format=%ct", revision)
        )
    generate(
        root, args.output_dir.resolve(), repository=args.repository, revision=revision, epoch=epoch
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
