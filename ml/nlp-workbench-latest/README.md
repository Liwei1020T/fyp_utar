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
- Never overwrite the protected V9 workbook or the backend's independent
  `output/latest_macbert_review_matrix_system12.xlsx` source from a notebook.
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
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

## NLP-01 data foundation

Create two independent, reproducible Data Audit, Cleaning, String Name
Canonicalization and Gold-template runs:

```bash
.venv/bin/python scripts/run_nlp01.py prepare \
  --run-id <nlp01-experiment-id> \
  --repeat 2 \
  --sample-size 450 \
  --seed 42
```

The command writes only to `output/runs/<run-id>/nlp01/`, leaves duplicates in
the clean dataset with explicit group IDs, records every exclusion reason, and
creates two blind annotation templates without exposing Silver labels. The
editable alias registry is `config/string_name_aliases.csv`; low-confidence
rows remain `pending` and cannot resolve a raw string automatically.

Validate a completed annotator file, merge two independent files, and export
adjudicated Gold with new run IDs:

```bash
.venv/bin/python scripts/run_nlp01.py validate \
  --input <annotator.csv> --require-complete

.venv/bin/python scripts/run_nlp01.py merge \
  --run-id <merge-run-id> \
  --annotator-a <annotator-a.csv> \
  --annotator-b <annotator-b.csv>

.venv/bin/python scripts/run_nlp01.py adjudicate \
  --run-id <gold-run-id> \
  --input <completed-adjudication-template.csv>
```

An optional Silver-assisted draft can reduce blank-label entry work, but it is
explicitly marked as automated and the merge gate refuses to treat it as human
Gold:

```bash
.venv/bin/python scripts/run_nlp01.py draft \
  --run-id <draft-run-id> \
  --template <annotator-template.csv> \
  --silver <run-specific-silver.csv>
```

Build a self-contained offline HTML for reviewing that draft and exporting the
current CSV state:

```bash
.venv/bin/python scripts/build_annotation_review_html.py \
  --run-id <html-review-run-id> \
  --draft <assistant-annotation-draft.csv> \
  --evidence <assistant-annotation-evidence.csv>
```

The HTML stores progress in browser local storage and can export/import a JSON
progress backup. Its CSV export remains marked `human_reviewed_ai_assisted` and
cannot be merged as independent blind human Gold.

## BERT pseudo-label baseline

When human Gold is unavailable, prepare a leakage-safe, high-confidence
three-class Silver pseudo-label dataset without changing its provenance.
Preparation keeps only `not_mentioned`, `positive`, and `negative` rows with
`needs_manual_review=0`; `mentioned` and `mixed` are excluded rather than forced
into training labels. It is limited to the 12 system strings in
`../../config/approved_string_cohort_v1.csv`; the 33-string raw source remains
unchanged:

```bash
.venv/bin/python scripts/prepare_bert.py \
  --run-id <unique-bert-prep-id> \
  --model-name hfl/chinese-macbert-base \
  --seed 42
```

This writes `bert_pseudo_labeled_dataset.csv`, `bert_dataset_report.json`, and
`bert_training_config.json` under `output/runs/<run-id>/bert/`. The source
label, high-confidence flag, manual-review flag, and
`rule_based_silver_not_human_gold` provenance remain visible on every row.

The active prepared cohort run is
`bert-prep-silver-overlap-longest-20260903`: 132,160 review-aspect rows from
16,184 reviews and 12 strings, split into 105,457 train, 13,220 validation, and
13,483 test rows with zero review/text/group partition crossings. Its frozen
dataset SHA-256 is
`9482b3ac7c1148270b37c981c46e3d5cfaeb6a9ccdbf877d665b56e673857bd2`.
The previous run remains available as immutable comparison evidence.

The experiment plan uses `google-bert/bert-base-chinese` as the academic
baseline and `hfl/chinese-macbert-base` as the primary model. After
bootstrapping the BERT dependencies, start with a bounded smoke run:

```bash
HF_HOME=/private/tmp/stringsense-hf-cache \
  .venv/bin/python scripts/train_bert.py \
  --run-id <unique-bert-training-id> \
  --dataset output/runs/<bert-prep-id>/bert/bert_pseudo_labeled_dataset.csv \
  --smoke-samples-per-split 500
```

Remove `--smoke-samples-per-split` only after the smoke run succeeds. The
training entry point uses aspect-conditioned input, inverse-frequency class
weights, deterministic seeds, early stopping on validation macro-F1, and writes
only to `output/runs/<run-id>/bert_training/`. Metrics measured against these
pseudo labels are pipeline-validation metrics, not human-ground-truth claims.

### Full training on Colab

The full run uses a Google Colab T4 session rather than the local CPU. Upload
only the prepared Silver CSV and minimum training code. Do not upload the raw
archive, historical `*_latest.csv` files, or the backend's protected current
matrix.

From the extracted portable workbench inside Colab, run:

```bash
python scripts/train_bert.py \
  --run-id <unique-full-training-id> \
  --dataset output/runs/<bert-prep-id>/bert/bert_pseudo_labeled_dataset.csv \
  --expected-dataset-sha256 <frozen-dataset-sha256> \
  --model-name hfl/chinese-macbert-base \
  --seed 42 \
  --max-length 128 \
  --epochs 3 \
  --train-batch-size 8 \
  --eval-batch-size 16
```

`--expected-dataset-sha256` activates the portable dataset-only boundary. The
training manifest records `input_boundary.mode=portable_dataset_sha256` and
`protected_source_assets_uploaded=false`; a digest mismatch fails before model
training. Download the complete run directory back into the matching local
`output/runs/<run-id>/` path before ending the Colab session.

The completed bounded method benchmark
`bert-benchmark-system12-high3-macbert-weighted-20260810-v1` used 5,000 rows per
split and reached pseudo-label test macro-F1 `0.86877`, including negative-class
F1 `0.71828`. This validates the weighted three-class method only; it is not the
final full-data result and is not human-Gold evaluation.

### Frozen-model offline inference

Predict one approved string/aspect input without writing runtime data:

```bash
.venv/bin/python scripts/infer_bert.py predict \
  --model-run-id bert-full-system12-longest-macbert-kaggle-20260903-v1 \
  --string "Yonex BG80" \
  --aspect control \
  --review-text "控球稳定，落点清楚" \
  --source-review-id smoke-control-001
```

Generate the full run-scoped candidate evidence chain:

```bash
.venv/bin/python scripts/infer_bert.py run \
  --run-id <unique-inference-run-id> \
  --model-run-id bert-full-system12-longest-macbert-kaggle-20260903-v1 \
  --dataset-run-id bert-prep-silver-overlap-longest-20260903
```

The command rechecks the frozen dataset digest, runs all 16,184 cohort reviews
against all nine aspects, records all three probabilities and low-confidence
exclusions, and writes only under `output/runs/<run-id>/bert_inference/`. Its
pilot threshold decision is based on held-out Silver error and coverage, not
human Gold or calibrated correctness. The resulting 12-by-9 matrix remains
`not_promoted`; importing it or changing the protected V9 workbook is a separate
approval task.

Review an immutable candidate without changing its threshold or importing it:

```bash
.venv/bin/python scripts/infer_bert.py review \
  --run-id <unique-review-run-id> \
  --source-run-id <inference-run-id>
```

The review run compares `0.99` and `0.995` separately on validation and test,
records Codex-assisted disagreement analysis pending project-owner confirmation,
adds descriptive cell-stability intervals, and runs ten fixed virtual-person
profiles through the backend's pure domain scorer. The run writes full rankings,
per-string Top 1/3/5 coverage, and descriptive near-tie outcomes without
reranking. Prices and official performance remain neutral/disabled in this
matrix-only comparison. It does not use the database, modify V9, choose a new
threshold, create Gold labels, calculate Kappa, or authorize promotion.

Try a lower threshold against the frozen probabilities without replacing the
confirmed pilot:

```bash
.venv/bin/python scripts/infer_bert.py sensitivity \
  --run-id <unique-sensitivity-run-id> \
  --source-run-id <inference-run-id> \
  --owner-confirmation-run-id <confirmation-run-id> \
  --confidence-threshold 0.8
```

The sensitivity run keeps the confirmed threshold and V9 immutable. It writes
only changed evidence statuses, a separate candidate Matrix, cell deltas, and
fixed-profile comparisons under its own `output/runs/<run-id>/` directory.

Compare the live scorer's default preference weights with the fixed squared
shadow variant using a read-only system catalog snapshot:

```bash
cd ../..
backend/.venv/bin/python backend/scripts/export_recommendation_catalog_snapshot.py \
  --output /private/tmp/stringsense-recommendation-catalog-snapshot.json

cd ml/nlp-workbench-latest
.venv/bin/python scripts/infer_bert.py optimize \
  --run-id <unique-optimization-run-id> \
  --source-run-id <inference-run-id> \
  --catalog-snapshot /private/tmp/stringsense-recommendation-catalog-snapshot.json
```

The exporter uses a read-only database transaction and includes the 12 approved
catalog rows, reviewed official performance, non-sensitive inventory prices,
and each row's `is_active` state. Cost prices and inventory notes are excluded.
The optimizer scores only `is_active=true` candidates, matching the live
repository boundary; rows without complete `manual_reviewed` official scores
remain NLP-backed. It compares exponent `1` with exponent `2` for the fixed
virtual profiles, but leaves the live scorer default unchanged and records
`selection_status=comparison_only_not_selected` and
`promotion.status=not_promoted`. Selecting the variant, enabling inactive
catalog rows, importing a Matrix, or changing V9 requires separate approval.

`merge` is unavailable until both files are complete. `adjudicate` refuses to
write `gold_dataset.csv` while any resolved label is missing or invalid. Having
templates is therefore not evidence that a human Gold Dataset exists.

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
├── nlp01/
│   ├── data_audit_report.json
│   ├── clean_reviews.csv
│   ├── confirmed_string_name_mappings.csv
│   ├── unresolved_string_names.csv
│   └── annotator_a_blind.csv / annotator_b_blind.csv
├── labeling/
│   ├── manifest.json
│   ├── nlp_absa_long_dataset.csv
│   └── nlp_absa_high_confidence.csv
├── pipeline/
│   ├── manifest.json
│   ├── run_summary.json
│   ├── model artifacts
│   └── versioned matrices and evidence CSVs
├── bert/
│   ├── bert_pseudo_labeled_dataset.csv
│   ├── bert_dataset_report.json
│   └── bert_training_config.json
├── bert_training/
│   ├── model/
│   ├── training_metrics.json
│   └── test_predictions.csv
├── run_manifest.json
└── execution_report.json
```

Experiment runs default to `promotion.status = "not_promoted"`. Comparing and
promoting an experiment artifact into backend runtime use is a separate task
that requires explicit human approval. The owner later clarified that MacBERT
must remain separate from V9. The current promotion is recorded by
`bert-macbert-longest-separate-matrix-promotion-20260903-v1`; the backend reads
the independent MacBERT Matrix from:

```text
output/latest_macbert_review_matrix_system12.xlsx
```

It contains exactly the approved 12 strings and nine MacBERT aspects and has
SHA256
`74ac92d891973fc1e7988d0ed27a4088eba9be0430d15ee8c774aac811d2050f`.
It was generated from model run
`bert-full-system12-longest-macbert-kaggle-20260903-v1` with weights SHA256
`82d95bb86d249850148691b6c8be801867d19354b0310a1c0f058dbb105f9e1f`.
The old V9 workbook remains unchanged at SHA256
`382d71cd90e195fcc41550c38175c13e1bb01515615fda572cf22fee90e05209`.
Runtime database import is complete: PostgreSQL contains 108 `nlp_review` rows
for the approved 12 strings and reports health status `imported`.

## Dataset summary

```json
{
  "strings_count": 33,
  "aspects_count": 9,
  "long_dataset_rows": 200250,
  "high_confidence_rows": 180555,
  "long_label_distribution": {
    "not_mentioned": 130294,
    "positive": 39132,
    "mentioned": 17441,
    "negative": 11129,
    "mixed": 2254
  },
  "high_label_distribution": {
    "not_mentioned": 130294,
    "positive": 39132,
    "negative": 11129
  }
}
```

The leakage-safe split groups by SHA-256 of normalized review text. All aspects
and duplicate normalized texts inherit one deterministic 80/10/10 partition.

The JSON above describes the preserved 33-string raw/historical source. The
current BERT training cohort is the approved 12-string subset and is documented
by its run-scoped manifest; neither scope should be substituted for the other.
