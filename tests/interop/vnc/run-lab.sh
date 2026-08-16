#!/bin/sh
set -eu

lab_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_root=$(CDPATH= cd -- "${lab_directory}/../../.." && pwd)
compose_file="${lab_directory}/compose.yml"

cleanup() {
    status=$?
    trap - EXIT INT TERM
    docker compose -f "$compose_file" down --volumes --remove-orphans \
        >/dev/null 2>&1 || true
    exit "$status"
}
trap cleanup EXIT INT TERM

export AARDWOLF_VNC_PROFILE="${AARDWOLF_VNC_PROFILE:-${lab_directory}/profile.example.yml}"

docker compose -f "$compose_file" up --build --detach --wait --wait-timeout 120

echo "Container TigerVNC package:"
docker compose -f "$compose_file" exec -T vnc \
    dpkg-query -W -f='${Package}=${Version}\n' tigervnc-standalone-server

cd "$repository_root"
"${PYTHON:-python3}" -m pytest tests/interop/vnc \
    --run-vnc \
    --capability protocol_probe \
    --capability vnc_password \
    --capability framebuffer \
    "$@"
