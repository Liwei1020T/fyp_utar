# StringSence Workspace

StringSence now lives as one integrated workspace that combines the mobile app, the unified Python backend, and the notebook-based NLP pipeline used to generate recommendation artifacts.

## Workspace Layout

- `mobile/`: Expo Router React Native app for player and admin flows
- `backend/`: FastAPI + SQLAlchemy backend and in-process AI/recommendation modules
- `ml/nlp-workbench/`: Jupyter notebook, datasets, and generated CSV outputs
- `docs/`: workspace-level documentation index

## Quick Start

### 1. Start the backend

```bash
cd backend
cp .env.example .env
uv sync --extra dev
./.venv/bin/alembic upgrade head
./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 3001 --reload
```

### 2. Start the mobile app

```bash
cd mobile
nvm use
npm install
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:3001/api npm run web
```

The mobile workspace pins Node `20.19.0` via `mobile/.nvmrc` and `mobile/package.json` allows the Node `20.x` line.

### 3. Run the NLP workbench when you need fresh recommendation artifacts

```bash
cd ml/nlp-workbench
python3 -m pip install -r requirements.txt
jupyter lab
```

Run `stringsense_complete_absa_pipeline_notebook.ipynb` from top to bottom. The generated outputs go into `ml/nlp-workbench/outputs/`.

## Backend and NLP Integration

- `backend/.env.example` points `AI_MATRIX_CSV_PATH` to `../ml/nlp-workbench/outputs/patched_practical_string_feature_matrix.csv`
- `backend/.env.example` points `AI_REVIEW_ASPECT_CSV_PATH` to `../ml/nlp-workbench/outputs/rule_based_review_aspect_signals.csv`
- If those generated files do not exist yet, the backend can still fall back to `backend/data/raw/badminton_strings_recommender.jsonl`

## Validation

- Mobile: `cd mobile && nvm use && npx tsc --noEmit`
- Backend: `cd backend && ./.venv/bin/ruff check . && ./.venv/bin/ruff format --check . && ./.venv/bin/mypy app ai_service tests && ./.venv/bin/pytest -v`

More detail lives in [docs/README.md](./docs/README.md), [mobile/README.md](./mobile/README.md), and [backend/README.md](./backend/README.md).
