#!/usr/bin/env bash
set -euo pipefail

# Uvicorn's reloader can accidentally watch `.venv/` and restart repeatedly when
# site-packages change. Keep reload scope limited to our source tree.
export WATCHFILES_IGNORE_PATHS=".venv,client/node_modules,client/dist"

exec uv run uvicorn main:app \
  --reload \
  --reload-dir app \
  --reload-dir tests \
  --host 0.0.0.0 \
  --port 8000

