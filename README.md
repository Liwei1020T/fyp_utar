# StringSence Workspace

StringSence now lives as one integrated workspace that combines the mobile app, the unified Python backend, and the notebook-based NLP pipeline used to generate recommendation artifacts.

## Workspace Layout

- `mobile/`: Expo Router React Native app for player and admin flows
- `backend/`: FastAPI + SQLAlchemy backend with the canonical in-process scorer at `backend/app/domain/recommendation/scoring.py`
- `ml/nlp-workbench-latest/`: canonical notebook package, datasets, and recommendation artifacts
- `docs/`: workspace-level documentation index

## Current Delivery Boundary

- Player/admin catalog, inventory, booking selection, recommendations, and BERT
  preparation share the 12-string boundary in
  `config/approved_string_cohort_v1.csv`.
- Other persisted or raw-source strings remain available only for historical
  booking, audit, and research provenance; they are hidden from active system
  flows rather than deleted.
- The current BERT task is aspect-conditioned, high-confidence Silver
  three-class classification: `not_mentioned`, `positive`, and `negative`.
  `mentioned` and `mixed` are excluded from training. No zero-shot NLI or human
  Gold claim is part of this bounded implementation.
- MacBERT training remains an offline Silver experiment. Its separately reviewed
  12-by-9 Matrix is promoted into the backend `nlp_review` layer; this promotion
  does not turn Silver validation into Gold, human accuracy, or Kappa evidence.

## Quick Start

### 1. Start Postgres

```bash
rtk docker compose up -d postgres
```

### 2. Start the backend

For browser-only testing on the same Mac, `127.0.0.1` is enough. For Expo Go on a phone, the backend must listen on `0.0.0.0` so the phone can reach it through the Mac Wi-Fi IP.

```bash
cd backend
cp .env.example .env
rtk uv sync --extra dev
rtk ./scripts/alembic upgrade head
rtk ./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

### 3. Start the mobile app in a browser

```bash
cd mobile
nvm use
npm install
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:3001/api npm run web
```

The mobile workspace pins Node `24.18.0` via `mobile/.nvmrc` and `mobile/package.json` allows the Node `24.x` LTS line.

### 4. Start the mobile app on Expo Go

Find the Mac Wi-Fi IP first. On this machine it usually appears as the `inet` value under `en0`.

```bash
rtk ifconfig en0
```

Then start Expo in LAN mode. Replace `<MAC_WIFI_IP>` with the IP from the previous command, for example `192.168.0.80`.

```bash
cd mobile
nvm use
EXPO_PUBLIC_API_BASE_URL=http://<MAC_WIFI_IP>:3001/api npm run start -- --lan
```

Open Expo Go on the phone and scan the QR code. The phone and Mac must be on the same Wi-Fi. Do not use `localhost` or `127.0.0.1` for Expo Go, because on a phone those addresses point to the phone itself, not the Mac.

### 5. Run the NLP workbench when you need fresh recommendation artifacts

```bash
cd ml/nlp-workbench-latest
./scripts/bootstrap.sh
.venv/bin/python -m pytest -q tests
.venv/bin/python scripts/run_experiment.py --run-id <experiment-id> --repeat 2
```

The runner executes labeling and the complete pipeline in order and writes only to immutable `output/runs/<run-id>/` directories. It fails on data leakage, protected-input changes, or non-reproducible metrics/CSV outputs.

The BERT path is documented separately in
[`ml/nlp-workbench-latest/README.md`](./ml/nlp-workbench-latest/README.md). Full
training may run on Colab GPU, but only the prepared Silver dataset and minimum
training code leave the workspace; raw review archives and protected `latest`
artifacts stay local.

Experiment outputs are never promoted automatically. The human-approved runtime source is the independent `ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx`; the protected V9 workbook remains separate and unchanged.

## Backend and NLP Integration

- `backend/.env.example` sets `RECOMMENDATION_MATRIX_SOURCE_PATH` to `../ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx`
- The unified FastAPI app uses the in-process scorer in `backend/app/domain/recommendation/scoring.py`
- If the NLP workbook does not exist, startup keeps persisted matrix rows when present and otherwise serves catalog/official-performance recommendations with health status `catalog_fallback`
- Fresh databases start with all business days closed and store identity, contact, address, and pricing explicitly unconfigured until an admin saves real values

## Validation

- Mobile: `cd mobile && nvm use && npm test && npx tsc --noEmit && npm run lint -- --max-warnings=0`
- Backend: `cd backend && ./.venv/bin/ruff check . && ./.venv/bin/ruff format --check . && ./.venv/bin/mypy app tests && ./.venv/bin/pytest -v`
- NLP: `cd ml/nlp-workbench-latest && .venv/bin/python -m pytest -q tests && .venv/bin/python scripts/run_experiment.py --run-id <experiment-id> --repeat 2`

More detail lives in [docs/README.md](./docs/README.md), [mobile/README.md](./mobile/README.md), and [backend/README.md](./backend/README.md). The current mock-data remediation status is recorded in [docs/plans/mock-page-remediation.md](./docs/plans/mock-page-remediation.md), and the latest complete customer and administrator browser evidence is in [docs/customer-admin-acceptance-2026-07-24.md](./docs/customer-admin-acceptance-2026-07-24.md). The earlier administrator-only acceptance remains in [docs/admin-acceptance-2026-07-23.md](./docs/admin-acceptance-2026-07-23.md), and the pre-FYP2 remediation gate remains preserved in [docs/plans/fyp2-readiness/04-remediation-results-and-readiness.md](./docs/plans/fyp2-readiness/04-remediation-results-and-readiness.md).
