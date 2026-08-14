#!/usr/bin/env bash
set -euo pipefail

SKIP_INSTALL=0
ENV_FILE="${NEIS_ENV_FILE:-}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-install)
      SKIP_INSTALL=1
      shift
      ;;
    --backend-host)
      BACKEND_HOST="$2"
      shift 2
      ;;
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --backend-port)
      BACKEND_PORT="$2"
      shift 2
      ;;
    --frontend-host)
      FRONTEND_HOST="$2"
      shift 2
      ;;
    --frontend-port)
      FRONTEND_PORT="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/backend"
FRONTEND_DIR="${REPO_ROOT}/frontend"

command -v python >/dev/null 2>&1 || { echo "python command not found" >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm command not found" >&2; exit 1; }

if [[ -n "${ENV_FILE}" ]]; then
  if [[ ! -f "${ENV_FILE}" ]]; then
    echo "Env file not found: ${ENV_FILE}" >&2
    exit 1
  fi
  export NEIS_ENV_FILE="${ENV_FILE}"
fi

export VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://${BACKEND_HOST}:${BACKEND_PORT}}"
export BACKEND_ALLOWED_ORIGINS="${BACKEND_ALLOWED_ORIGINS:-http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}}"

if [[ "${SKIP_INSTALL}" -eq 0 ]]; then
  (cd "${BACKEND_DIR}" && python -m pip install -e ".[dev]")
  if [[ -f "${FRONTEND_DIR}/package-lock.json" ]]; then
    (cd "${FRONTEND_DIR}" && npm ci)
  else
    (cd "${FRONTEND_DIR}" && npm install)
  fi
fi

cleanup() {
  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "${FRONTEND_PID}" 2>/dev/null || true
  fi
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "${BACKEND_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

(cd "${BACKEND_DIR}" && python -m uvicorn app.main:app --reload --app-dir src --host "${BACKEND_HOST}" --port "${BACKEND_PORT}") &
BACKEND_PID=$!

(cd "${FRONTEND_DIR}" && npm run dev -- --host "${FRONTEND_HOST}" --port "${FRONTEND_PORT}") &
FRONTEND_PID=$!

echo "Backend:  http://${BACKEND_HOST}:${BACKEND_PORT}"
echo "Frontend: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo "Press Ctrl+C to stop."

wait -n "${BACKEND_PID}" "${FRONTEND_PID}"
