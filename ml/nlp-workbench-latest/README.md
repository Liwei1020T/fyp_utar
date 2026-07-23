# NLP Workbench Latest — Canonical Experiment Root

This is the approved offline NLP workspace for StringSence. The notebooks are
thin, inspectable entry points over the tested code in `src/stringsense_nlp/`;
they are not a public service and do not replace the backend scorer.

## Immutable boundary

- Read only `data/archive_latest/badminton_strings_data.json` as the raw review
  source. Never open, extract, hash, or rewrite `data/archive_latest.zip`.
- Treat the V8 dictionary and normalization rules as read-only inputs.
- Preserve every `data/*_latest.csv` as historical evidence. The two ABSA
  `*_latest.csv` files predate the leakage-safe split and are not training inputs.
- Never overwrite the backend's current canonical artifact at
  `output/latest_practical_string_feature_matrix_v9_v8dict.xlsx` from a notebook.
- Create experiment artifacts only under `output/runs/<run-id>/`. That directory
  is ignored by Git and every stage is create-once.

Each run records SHA-256 fingerprints for readable inputs and protected assets.
The ZIP is verified with metadata only so the pipeline never reads its content.

## Environment

The workbench pins Python 3.13 in `.python-version`. Bootstrap the isolated
environment from the exact, hash-locked dependency set:

```bash
cd ml/nlp-workbench-latest
./scripts/bootstrap.sh
```

`requirements.in` contains direct dependencies. `requirements.txt` is the
generated lock. Only regenerate it as an intentional dependency change:

```bash
UV_CACHE_DIR=/private/tmp/stringsense-nlp-uv-cache \
  uv pip compile requirements.in --python 3.13 --generate-hashes \
  --output-file requirements.txt
```

The bootstrap uses `uv` to select Python and `pip --require-hashes` to install.
That combination avoids the external-volume AppleDouble metadata issue while
retaining exact package and artifact verification.

## Validate and run

Run the fast gate first:

```bash
.venv/bin/python -m pytest -q tests
../../backend/.venv/bin/ruff check src scripts tests --exclude '._*' --exclude '**/._*'
../../backend/.venv/bin/ruff format --check src scripts tests --exclude '._*' --exclude '**/._*'
```

Then execute both canonical notebooks twice with the same experiment base ID:

```bash
.venv/bin/python scripts/run_experiment.py \
  --run-id <experiment-id> \
  --repeat 2
```

The runner executes labeling before the pipeline, uses the `stringsense-nlp`
kernel, rejects existing stage directories, checks every leakage gate, verifies
protected assets, and fails unless metrics and all CSV hashes match across both
runs. Jupyter may report that its short-lived local kernel uses TCP; the runner
does not expose an application port and immediately closes each kernel.

For interactive inspection, export one unused `STRINGSENSE_NLP_RUN_ID`, open
Jupyter Lab, and run the labeling notebook before the complete pipeline notebook.
Do not reuse a run ID.

## Run layout and promotion

```text
output/runs/<run-id>/
├── labeling/
│   ├── manifest.json
│   ├── nlp_absa_long_dataset.csv
│   └── nlp_absa_high_confidence.csv
├── pipeline/
│   ├── manifest.json
│   ├── run_summary.json
│   ├── model artifacts
│   └── versioned matrices and evidence CSVs
├── run_manifest.json
└── execution_report.json
```

Every run manifest ends with `promotion.status = "not_promoted"`. Comparing and
promoting an experiment artifact to the backend V9 workbook is a separate task
that requires explicit human approval. The backend continues to use:

```text
output/latest_practical_string_feature_matrix_v9_v8dict.xlsx
```

## Dataset summary

```json
{
  "strings_count": 33,
  "aspects_count": 9,
  "long_dataset_rows": 200250,
  "high_confidence_rows": 178219,
  "long_label_distribution": {
    "not_mentioned": 130296,
    "positive": 38712,
    "mentioned": 17441,
    "negative": 9211,
    "mixed": 4590
  },
  "high_label_distribution": {
    "not_mentioned": 130296,
    "positive": 38712,
    "negative": 9211
  }
}
```

The leakage-safe split groups by SHA-256 of normalized review text. All aspects
and duplicate normalized texts inherit one deterministic 80/10/10 partition.
