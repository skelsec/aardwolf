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

export AARDWOLF_XRDP_PROFILE="${AARDWOLF_XRDP_PROFILE:-${lab_directory}/profile.example.yml}"

docker compose -f "$compose_file" up --build --detach --wait --wait-timeout 120

echo "Container xrdp package:"
docker compose -f "$compose_file" exec -T xrdp \
    dpkg-query -W -f='${Package}=${Version}\n' xrdp xorgxrdp

cd "$repository_root"
"${PYTHON:-python3}" -m pytest tests/interop/xrdp \
    --run-xrdp \
    --capability protocol_probe \
    --capability rdp_plain \
    --capability screenshot \
    --capability keyboard_mouse \
    "$@"
