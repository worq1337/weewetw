#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_REQ="$REPO_ROOT/backend/tbcparcer_api/requirements.txt"
FRONTEND_DIR="$REPO_ROOT/frontend/tbcparcer-frontend"

if [[ -f "$BACKEND_REQ" ]]; then
  echo "Installing backend dependencies from $BACKEND_REQ"
  python3 -m pip install -r "$BACKEND_REQ"
else
  echo "Backend requirements file not found at $BACKEND_REQ" >&2
  exit 1
fi

if command -v pnpm >/dev/null 2>&1; then
  echo "Installing frontend dependencies in $FRONTEND_DIR"
  (cd "$FRONTEND_DIR" && pnpm install)
else
  echo "pnpm is not installed. Please install pnpm to continue." >&2
  exit 1
fi
