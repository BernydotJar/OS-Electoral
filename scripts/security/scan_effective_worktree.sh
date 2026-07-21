#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
SNAPSHOT=$(mktemp -d)
cleanup() {
  rm -rf "$SNAPSHOT"
}
trap cleanup EXIT HUP INT TERM

command -v git >/dev/null 2>&1 || {
  echo "git is required for the effective-worktree secret scan" >&2
  exit 2
}
command -v gitleaks >/dev/null 2>&1 || {
  echo "gitleaks is required for the effective-worktree secret scan" >&2
  exit 2
}
command -v python3 >/dev/null 2>&1 || {
  echo "python3 is required for the effective-worktree secret scan" >&2
  exit 2
}

cd "$ROOT"
python3 - "$SNAPSHOT" <<'PY'
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

root = Path.cwd()
snapshot = Path(sys.argv[1])
raw = subprocess.check_output(
    ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
)
for encoded in raw.split(b"\0"):
    if not encoded:
        continue
    relative = Path(os.fsdecode(encoded))
    source = root / relative
    if not source.exists() and not source.is_symlink():
        continue
    target = snapshot / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        target.symlink_to(os.readlink(source))
    elif source.is_file():
        shutil.copy2(source, target)
PY

gitleaks dir \
  --no-banner \
  --redact \
  --config "$ROOT/.gitleaks.toml" \
  "$SNAPSHOT"

echo "[OK] effective tracked and non-ignored worktree contains no detected secrets"
