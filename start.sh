#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

DEFAULT_DESIGN_DIR="examples/expected/background-export"
DESIGN_DIR="${JOURNEYMAN_DESIGN_DIR:-$DEFAULT_DESIGN_DIR}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8765}"
CHECK_ONLY=0

log() { printf '[start] %s\n' "$*"; }
die() { printf '[start][error] %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

usage() {
  cat <<'USAGE'
Usage: ./start.sh [design-dir] [--host HOST] [--port PORT] [--check]

Runs the read-only Journeyman dashboard for a design artifact directory.

Environment:
  JOURNEYMAN_DESIGN_DIR  Default design directory when no positional argument is given.
  HOST                   Dashboard bind host. Default: 127.0.0.1.
  PORT                   Preferred dashboard port. Default: 8765.
  JOURNEYMAN_VENV_DIR    Repo-local virtualenv path. Default: .venv.
  SKIP_START_TESTS=1     Skip preflight fixture validation.
USAGE
}

while (($#)); do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --check|--check-only|--no-launch)
      CHECK_ONLY=1
      shift
      ;;
    --host)
      [[ $# -ge 2 ]] || die "--host requires a value"
      HOST="$2"
      shift 2
      ;;
    --port)
      [[ $# -ge 2 ]] || die "--port requires a value"
      PORT="$2"
      shift 2
      ;;
    --*)
      die "Unknown option: $1"
      ;;
    *)
      DESIGN_DIR="$1"
      shift
      ;;
  esac
done

port_in_use() {
  local port="$1"
  if have lsof; then
    lsof -tiTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
  elif have ss; then
    ss -ltn | awk '{print $4}' | grep -Eq "(^|[:.])${port}$"
  elif have nc; then
    nc -z 127.0.0.1 "$port" >/dev/null 2>&1
  else
    (echo >"/dev/tcp/127.0.0.1/$port") >/dev/null 2>&1
  fi
}

choose_port() {
  local requested="$1" max_offset="${2:-20}" port
  port="$requested"
  [[ "$requested" =~ ^[0-9]+$ ]] || die "PORT must be numeric, got: $requested"
  while port_in_use "$port"; do
    port=$((port + 1))
    if ((port > requested + max_offset)); then
      die "No free port found in range ${requested}-$((requested + max_offset))"
    fi
  done
  printf '%s\n' "$port"
}

ensure_python() {
  have python3 || die "python3 is required to run Journeyman"
  local venv_dir="${JOURNEYMAN_VENV_DIR:-$ROOT_DIR/.venv}"
  if [[ ! -x "$venv_dir/bin/python" ]]; then
    log "Creating repo-local Python virtualenv at ${venv_dir#$ROOT_DIR/}"
    python3 -m venv "$venv_dir"
  fi
  PYTHON="$venv_dir/bin/python"
  export PYTHON
}

ensure_dependencies() {
  if "$PYTHON" -c 'import journeyman, yaml' >/dev/null 2>&1; then
    return 0
  fi
  log "Installing Journeyman into the repo-local virtualenv"
  "$PYTHON" -m pip install -e .
}

validate_design_dir() {
  [[ -d "$DESIGN_DIR" ]] || die "Design directory does not exist: $DESIGN_DIR"
  [[ -f "$DESIGN_DIR/requirements.raw.md" ]] || die "Missing requirements.raw.md in: $DESIGN_DIR"
}

run_preflight_tests() {
  if [[ "${SKIP_START_TESTS:-0}" == "1" ]]; then
    log "Skipping preflight validation because SKIP_START_TESTS=1"
    return 0
  fi

  log "Running startup preflight validation"
  if "$PYTHON" -m pytest --version >/dev/null 2>&1; then
    "$PYTHON" -m pytest -q -p no:cacheprovider
    return 0
  fi

  "$PYTHON" - <<'PY'
from pathlib import Path
from journeyman.validator import validate_design, validate_hashes

cases = [
    Path("examples/expected/password-reset"),
    Path("examples/expected/background-export"),
    Path("examples/expected/commit-message"),
]

for case in cases:
    design = validate_design(case)
    hashes = validate_hashes(case)
    if not design.ok:
        raise SystemExit(f"{case}: validation failed: {design.errors}")
    if not hashes.ok:
        raise SystemExit(f"{case}: hash check failed: {hashes.errors}")
PY
}

ensure_python
ensure_dependencies
validate_design_dir
run_preflight_tests

if ((CHECK_ONLY)); then
  log "Startup check passed for $DESIGN_DIR"
  exit 0
fi

APP_PORT="$(choose_port "$PORT")"
export PORT="$APP_PORT"
log "Launching Journeyman dashboard for $DESIGN_DIR"
log "Dashboard URL: http://$HOST:$APP_PORT"

exec "$PYTHON" -m journeyman.cli dashboard "$DESIGN_DIR" --host "$HOST" --port "$APP_PORT"
