#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKBENCH_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
UV_CACHE_DIR="${UV_CACHE_DIR:-/private/tmp/stringsense-nlp-uv-cache}"
export UV_CACHE_DIR

cd "$WORKBENCH_DIR"
uv venv --python 3.13 --allow-existing .venv
.venv/bin/python -m ensurepip --upgrade
.venv/bin/python -m pip install --require-hashes -r requirements.txt
if command -v dot_clean >/dev/null 2>&1; then
  dot_clean -m .venv/lib/python3.13/site-packages
fi
.venv/bin/python -m ipykernel install \
  --prefix .venv \
  --name stringsense-nlp \
  --display-name "StringSense NLP"

printf 'NLP environment ready: %s\n' "$WORKBENCH_DIR/.venv"
