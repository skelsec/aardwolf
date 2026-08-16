#!/bin/sh
# Create the test environment, run a named suite, and always tear labs down.
# You do not need to manage a venv, Docker Compose, or pytest flags yourself.
#
#   ./run-tests.sh              offline baseline
#   ./run-tests.sh full         baseline plus disposable xrdp and VNC labs
#   ./run-tests.sh --help

set -eu

repository_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$repository_root"

profile="baseline"
fresh=0
ephemeral=0
with_coverage=0
pytest_args=""
venv_dir=""
python=""
status=0

usage() {
    cat <<'EOF'
Usage: ./run-tests.sh [profile] [options] [-- pytest-args]

Creates a managed test venv, installs aardwolf plus test deps, runs the
selected suite, and always stops disposable Docker labs afterward.

Profiles
  baseline       Offline unit + fake-peer + component (default)
  unit           Offline unit tests only
  full           Baseline plus xrdp and VNC labs
  lab            Both disposable labs
  xrdp           xrdp lab only
  vnc            TigerVNC lab only
  destructive    Labs with --run-destructive and --run-slow
  rust           cargo test for the native codec crates
  clean          Remove the managed venv and stop leftover lab containers

Options
  --fresh        Recreate the managed venv before installing
  --ephemeral    Throwaway venv deleted on exit (even on success)
  --cov          Branch coverage for Python suites
  -h, --help     Show this help

Examples
  ./run-tests.sh
  ./run-tests.sh full
  ./run-tests.sh xrdp -- -k login -vv
  ./run-tests.sh baseline --cov
EOF
}

need_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "run-tests: missing required command: $1" >&2
        exit 2
    fi
}

python_is_new_enough() {
    "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'
}

venv_fingerprint() {
    cat \
        pyproject.toml \
        requirements-test.txt \
        rust/Cargo.lock \
        rust/rle/Cargo.toml \
        rust/bulk-compression/Cargo.toml \
        rust/rle/rle.rs \
        rust/bulk-compression/src/*.rs \
        2>/dev/null | sha256sum | awk '{print $1}'
}

stop_labs() {
    if ! command -v docker >/dev/null 2>&1; then
        return 0
    fi
    docker compose -f tests/interop/xrdp/compose.yml down --volumes --remove-orphans \
        >/dev/null 2>&1 || true
    docker compose -f tests/interop/vnc/compose.yml down --volumes --remove-orphans \
        >/dev/null 2>&1 || true
}

cleanup() {
    saved=$?
    trap - EXIT INT TERM
    stop_labs
    if [ "$ephemeral" -eq 1 ] && [ -n "$venv_dir" ] && [ -d "$venv_dir" ]; then
        rm -rf "$venv_dir"
    fi
    if [ "$status" -eq 0 ]; then
        status=$saved
    fi
    exit "$status"
}

prepare_venv() {
    need_cmd cargo
    if [ "$ephemeral" -eq 1 ]; then
        venv_dir=$(mktemp -d "${TMPDIR:-/tmp}/aardwolf-test.XXXXXX")
    else
        venv_dir="${repository_root}/.venv-test"
    fi

    fingerprint=$(venv_fingerprint)
    stamp="${venv_dir}/.aardwolf-test-stamp"
    if [ "$fresh" -eq 1 ] && [ -d "$venv_dir" ]; then
        rm -rf "$venv_dir"
    fi
    if [ ! -x "${venv_dir}/bin/python" ]; then
        echo "run-tests: creating venv at ${venv_dir}"
        "$PYTHON_BIN" -m venv "$venv_dir"
    fi
    python="${venv_dir}/bin/python"
    if [ ! -f "$stamp" ] || [ "$(cat "$stamp")" != "$fingerprint" ]; then
        echo "run-tests: installing aardwolf and test dependencies"
        "$python" -m pip install --upgrade pip
        "$python" -m pip install -e "$repository_root"
        "$python" -m pip install -r "$repository_root/requirements-test.txt"
        printf '%s\n' "$fingerprint" > "$stamp"
    else
        echo "run-tests: reusing venv at ${venv_dir}"
    fi
    export PYTHON="$python"
}

coverage_args() {
    if [ "$with_coverage" -eq 1 ]; then
        printf '%s\n' \
            --cov=aardwolf \
            --cov-branch \
            --cov-report=term-missing \
            --cov-report=xml:reports/coverage.xml
    fi
}

run_pytest() {
    mkdir -p reports test-results
    # shellcheck disable=SC2086
    PYTHONHASHSEED=0 "$python" -m pytest "$@" $pytest_args
}

run_offline() {
    echo "run-tests: offline suite"
    # shellcheck disable=SC2046
    run_pytest tests/unit tests/fake_peer tests/component \
        --junitxml=test-results/junit.xml \
        $(coverage_args)
}

run_unit() {
    echo "run-tests: unit suite"
    # shellcheck disable=SC2046
    run_pytest tests/unit \
        --junitxml=test-results/junit-unit.xml \
        $(coverage_args)
}

run_xrdp() {
    need_cmd docker
    docker compose version >/dev/null
    echo "run-tests: xrdp lab (always torn down)"
    # shellcheck disable=SC2086
    tests/interop/xrdp/run-lab.sh "$@" $pytest_args
}

run_vnc() {
    need_cmd docker
    docker compose version >/dev/null
    echo "run-tests: VNC lab (always torn down)"
    # shellcheck disable=SC2086
    tests/interop/vnc/run-lab.sh "$@" $pytest_args
}

run_rust() {
    need_cmd cargo
    echo "run-tests: rust codec tests"
    (
        cd rust
        PYO3_NO_PYTHON=1 cargo test --workspace
    )
}

first_failure() {
    if [ "$1" -ne 0 ]; then
        echo "$1"
    else
        echo "$2"
    fi
}

while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        --fresh)
            fresh=1
            shift
            ;;
        --ephemeral)
            ephemeral=1
            shift
            ;;
        --cov)
            with_coverage=1
            shift
            ;;
        --)
            shift
            pytest_args="$*"
            break
            ;;
        baseline|unit|full|lab|interop|xrdp|vnc|destructive|rust|clean)
            profile=$1
            shift
            ;;
        -*)
            pytest_args="${pytest_args:+$pytest_args }$1"
            shift
            ;;
        *)
            echo "run-tests: unknown argument: $1" >&2
            echo "Try ./run-tests.sh --help" >&2
            exit 2
            ;;
    esac
done

if [ "$profile" = "interop" ]; then
    profile="lab"
fi

PYTHON_BIN=${PYTHON:-python3}
need_cmd "$PYTHON_BIN"
if ! python_is_new_enough "$PYTHON_BIN"; then
    echo "run-tests: Python 3.11 or newer is required (found $($PYTHON_BIN -c 'import sys; print(sys.version.split()[0])'))" >&2
    exit 2
fi

trap cleanup EXIT INT TERM

case "$profile" in
    clean)
        echo "run-tests: stopping labs and removing .venv-test"
        stop_labs
        rm -rf "${repository_root}/.venv-test"
        status=0
        ;;
    rust)
        run_rust || status=$?
        ;;
    baseline)
        prepare_venv
        run_offline || status=$?
        ;;
    unit)
        prepare_venv
        run_unit || status=$?
        ;;
    xrdp)
        prepare_venv
        run_xrdp || status=$?
        ;;
    vnc)
        prepare_venv
        run_vnc || status=$?
        ;;
    lab)
        prepare_venv
        xrdp_status=0
        vnc_status=0
        run_xrdp || xrdp_status=$?
        run_vnc || vnc_status=$?
        status=$(first_failure "$xrdp_status" "$vnc_status")
        ;;
    full)
        prepare_venv
        offline_status=0
        xrdp_status=0
        vnc_status=0
        run_offline || offline_status=$?
        run_xrdp || xrdp_status=$?
        run_vnc || vnc_status=$?
        status=$(first_failure "$offline_status" "$(first_failure "$xrdp_status" "$vnc_status")")
        ;;
    destructive)
        prepare_venv
        xrdp_status=0
        vnc_status=0
        run_xrdp --run-destructive --run-slow || xrdp_status=$?
        run_vnc --run-destructive --run-slow || vnc_status=$?
        status=$(first_failure "$xrdp_status" "$vnc_status")
        ;;
    *)
        echo "run-tests: unknown profile: $profile" >&2
        exit 2
        ;;
esac
