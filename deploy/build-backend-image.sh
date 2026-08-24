#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
IMAGE_TAG=${1:-stringsense-backend:production}

cd "$PROJECT_ROOT"
export COPYFILE_DISABLE=1

tar -cf - \
  --exclude='._*' \
  --exclude='*/._*' \
  --exclude='*/.__*' \
  --exclude='*/__pycache__' \
  Dockerfile.backend \
  backend/pyproject.toml \
  backend/uv.lock \
  backend/alembic.ini \
  backend/app \
  backend/migrations \
  backend/data/string_catalog_db_ready.json \
  config/approved_string_cohort_v1.csv \
  ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx \
  | docker build --file Dockerfile.backend --tag "$IMAGE_TAG" -
