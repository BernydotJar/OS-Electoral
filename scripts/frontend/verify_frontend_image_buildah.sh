#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
FRONTEND_DIR="$ROOT/frontend"
IMAGE_TAG=${CAMPAIGNOS_FRONTEND_IMAGE_TAG:-campaignos-frontend:c3-front-001-buildah}

command -v buildah >/dev/null 2>&1 || {
  echo "buildah is required for daemonless frontend image verification" >&2
  exit 2
}
command -v python3 >/dev/null 2>&1 || {
  echo "python3 is required for frontend image metadata verification" >&2
  exit 2
}

export STORAGE_DRIVER=vfs
export BUILDAH_ISOLATION=chroot

buildah bud \
  --format docker \
  --isolation chroot \
  --storage-driver vfs \
  --network host \
  --layers=false \
  --file "$FRONTEND_DIR/Dockerfile" \
  --tag "$IMAGE_TAG" \
  "$FRONTEND_DIR"

IMAGE_JSON=$(mktemp)
CONTAINER=
cleanup() {
  rm -f "$IMAGE_JSON"
  if [ -n "$CONTAINER" ]; then
    buildah rm --storage-driver vfs "$CONTAINER" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT HUP INT TERM

buildah inspect --storage-driver vfs --type image "$IMAGE_TAG" > "$IMAGE_JSON"
python3 - "$IMAGE_JSON" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    image = json.load(handle)
config = image.get("Docker", {}).get("config", {})
healthcheck = config.get("Healthcheck", {})
assert config.get("User") == "10001:10001", config.get("User")
assert config.get("Cmd") == ["node", "server.js"], config.get("Cmd")
assert healthcheck.get("Test", [])[:1] == ["CMD"], healthcheck
print(
    json.dumps(
        {
            "image_id": image.get("FromImageID") or image.get("ID"),
            "user": config.get("User"),
            "cmd": config.get("Cmd"),
            "healthcheck": healthcheck,
        },
        indent=2,
    )
)
PY

CONTAINER=$(buildah from --storage-driver vfs "$IMAGE_TAG")
buildah config \
  --storage-driver vfs \
  --env CAMPAIGNOS_FRONTEND_MODE=demo_read_only \
  --env CAMPAIGNOS_FRONTEND_ENVIRONMENT=test \
  "$CONTAINER"

buildah run \
  --storage-driver vfs \
  --isolation chroot \
  --network host \
  "$CONTAINER" \
  -- /bin/sh -c '
    node server.js >/tmp/campaignos-frontend.log 2>&1 &
    pid=$!
    ready=0
    for attempt in 1 2 3 4 5 6 7 8 9 10; do
      if wget -q -O /tmp/campaignos-page http://127.0.0.1:3000/es; then
        ready=1
        break
      fi
      sleep 1
    done
    test "$ready" = 1
    grep -q "Centro de mando gobernado" /tmp/campaignos-page
    grep -q "DEMO SINT" /tmp/campaignos-page
    kill "$pid"
    wait "$pid" 2>/dev/null || true
    cat /tmp/campaignos-frontend.log
  '

echo "[OK] daemonless frontend image build, metadata, health contract and smoke test"
