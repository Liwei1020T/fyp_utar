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
- Runtime seeding filters the 33-item source snapshot through that cohort before
  creating rows, so a fresh database contains only 12 catalog, inventory, and
  recommendation candidates. The remaining source records are offline research
  provenance, not runtime database rows.
- Existing non-approved runtime rows are removed by migration
  `20260902_0042`; `store_settings`, business hours, the approved strings, and
  their active inventory are preserved.
- The current BERT task is aspect-conditioned, high-confidence Silver
  three-class classification: `not_mentioned`, `positive`, and `negative`.
  `mentioned` and `mixed` are excluded from training. No zero-shot NLI or human
  Gold claim is part of this bounded implementation.
- MacBERT training remains an offline Silver experiment. Its separately reviewed
  12-by-9 Matrix is promoted into the backend `nlp_review` layer; this promotion
  does not turn Silver validation into Gold, human accuracy, or Kappa evidence.
- Profile recommendation generation persists cache and run-audit rows. Agent
  What-if previews return an ephemeral `run_id` but do not persist a run, cache,
  or profile changes.

## Documentation Map

- Start with [AGENTS.md](./AGENTS.md) for repository rules, ownership
  boundaries, and validation commands.
- Use [docs/README.md](./docs/README.md) to find current architecture and
  operations guides. Dated acceptance records and plans are evidence of a past
  check or decision; they are not a replacement for the current README or
  source code.
- Use [deploy/README.md](./deploy/README.md) only for the controlled Docker and
  Cloudflare deployment path. It is not a statement that a live public tunnel
  or provider integration has been verified.

## Quick Start

### Run the full application with Docker

This starts PostgreSQL, the FastAPI backend, Alembic migration, and Expo Web
in Docker containers. Keep `backend/.env` configured for local development.

```bash
DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=1 docker compose -p stringsence -f compose.yaml -f compose.local.yaml up -d --build postgres migrate backend frontend
docker compose -p stringsence -f compose.yaml -f compose.local.yaml ps
curl http://127.0.0.1:3001/health
```

Open [http://127.0.0.1:8081](http://127.0.0.1:8081) for the frontend. Stop the
containers without deleting the database volume with:

```bash
docker compose -p stringsence -f compose.yaml -f compose.local.yaml down
```

### 1. Start Postgres

```bash
docker compose up -d postgres
```

### 2. Start the backend

For browser-only testing on the same Mac, `127.0.0.1` is enough. For Expo Go on a phone, the backend must listen on `0.0.0.0` so the phone can reach it through the Mac Wi-Fi IP.

```bash
cd backend
cp .env.example .env
uv sync --extra dev
./scripts/alembic upgrade head
./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
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
ifconfig en0
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
- Fresh databases restore the configured single-store profile and weekly schedule from `backend/data/store_settings_seed.json`; later admin edits remain database-owned

## Validation

- Mobile: `cd mobile && nvm use && npm test && npx tsc --noEmit && npm run lint -- --max-warnings=0`
- Backend: `cd backend && ./.venv/bin/ruff check . && ./.venv/bin/ruff format --check . && ./.venv/bin/mypy app tests && ./.venv/bin/pytest -v`
- NLP: `cd ml/nlp-workbench-latest && .venv/bin/python -m pytest -q tests && .venv/bin/python scripts/run_experiment.py --run-id <experiment-id> --repeat 2`

More detail lives in [docs/README.md](./docs/README.md),
[mobile/README.md](./mobile/README.md), and
[backend/README.md](./backend/README.md). The dated acceptance records and
plans linked from the docs index remain useful evidence, but do not establish
current device, provider, tunnel, or deployment availability.
