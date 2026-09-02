# BERT ABSA Review Optimization Design

## Status

Full-data MacBERT training completed on Colab T4 on 2026-08-10. Offline
inference and Matrix review subsequently completed. On 2026-08-12, the project
owner clarified that MacBERT must not be merged into the old V9 workbook.
Promotion run `bert-macbert-separate-matrix-promotion-20260812-v1` restored V9
to its original artifact and promoted an independent 12-by-9 MacBERT Matrix.
Docker/Postgres has recovered and the independent Matrix is imported as 108
`nlp_review` rows across the approved 12 strings. The current schema head is
`20260902_0045`; the earlier head named in the original promotion evidence is
historical.

This document supersedes the broader 2026-05-31 proposal. The active scope is a
small FYP-ready Silver baseline, not the earlier two-stage five-class, mandatory
Gold, or 33-string delivery plan.

## Decision Summary

- Use only the 12 strings in `config/approved_string_cohort_v1.csv` throughout
  active catalog flows, BERT training, matrix generation, and recommendation
  comparison.
- Keep the 33-string raw source unchanged for historical and research
  provenance. The other strings are hidden from the system, not deleted.
- Train one aspect-conditioned three-class classifier with labels
  `not_mentioned`, `positive`, and `negative`.
- Use only high-confidence rule-based Silver rows with
  `needs_manual_review=0`. Exclude `mentioned` and `mixed` instead of coercing
  them into a class.
- Use `hfl/chinese-macbert-base` with inverse-frequency weighted cross entropy.
- Do not use zero-shot NLI.
- Do not claim human Gold, independent annotation, Cohen's Kappa, or
  human-ground-truth accuracy.
- Run the full model offline on Colab T4 and return all outputs to an immutable
  local `output/runs/<run-id>/` directory.
- Generate a reviewed 12-by-9 matrix after full training; do not overwrite the
  current V9 workbook automatically.
- Link future system feedback through offline batch inference and the existing
  recommendation-matrix importer, without deploying a separate AI service.

## Goal

Use review text to create traceable item-side signals for nine badminton-string
aspects while keeping the current backend recommender and runtime architecture
stable.

The nine aspects are:

1. `attack`
2. `comfort`
3. `control`
4. `durability`
5. `elasticity`
6. `sound`
7. `string_movement`
8. `tension_retention`
9. `value_for_money`

## Non-goals

- Human Gold annotation or Kappa reporting
- Zero-shot NLI labeling
- Five-class prediction
- Training or publishing models for all 33 raw-source strings
- Real-time MacBERT inference inside the feedback POST request
- Automatic model retraining from new customer comments
- Automatic promotion of model scores into production runtime data
- Rewriting the backend recommendation scorer

## System and Data Boundary

### Active cohort

`config/approved_string_cohort_v1.csv` is the shared boundary for the backend
and BERT preparation:

- Yonex BG80
- Yonex BG65
- Yonex BG66 ULTIMAX
- Yonex BG80 POWER
- Yonex EXBOLT 63
- Yonex AEROBITE
- Victor VBS-66 NANO
- Victor VBS-68 Power
- Li-Ning No.1
- Li-Ning N65
- Gosen RYZONIC 65
- Kumpoo JS-63

### Raw and protected inputs

- Raw review JSON:
  `ml/nlp-workbench-latest/data/archive_latest/badminton_strings_data.json`
- Domain dictionary:
  `ml/nlp-workbench-latest/data/domain_dictionary_optimized_v8.csv`
- Normalization rules:
  `ml/nlp-workbench-latest/data/normalization_rules_v8.csv`
- Current backend MacBERT review matrix:
  `ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx`
- Preserved legacy V9 workbook:
  `ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v9_v8dict.xlsx`

The ZIP archive, historical `*_latest.csv` files, MacBERT Matrix, and legacy V9
workbook are protected assets. Experiments do not rewrite them.

### Prepared training dataset

Current preparation run:

```text
bert-prep-system12-high3-20260810-v1
```

Verified facts:

| Field | Value |
| --- | ---: |
| Strings | 12 |
| Reviews | 16,184 |
| Review-aspect rows | 130,421 |
| Train rows | 104,045 |
| Validation rows | 13,077 |
| Test rows | 13,299 |
| `not_mentioned` | 95,455 |
| `positive` | 28,127 |
| `negative` | 6,839 |

Dataset SHA-256:

```text
64ff725a7f38696cb21a178249b3ce642c4f8bb99485a914b8beff80af89754d
```

The split groups by normalized review text and records zero review, text, or
group crossings. Every row retains
`annotation_provenance=rule_based_silver_not_human_gold`.

## Model Design

Each training row is one target string, one aspect, and one review:

```text
目标球线：<canonical string name>
评价方面：<Chinese aspect description>
评论：<review text>
```

Output labels:

| ID | Label | Meaning |
| ---: | --- | --- |
| 0 | `not_mentioned` | The review does not provide evidence for this aspect. |
| 1 | `positive` | The review expresses positive evidence for this aspect. |
| 2 | `negative` | The review expresses negative evidence for this aspect. |

Training configuration:

- Model: `hfl/chinese-macbert-base`
- Seed: `42`
- Maximum sequence length: `128` for the approved full run
- Epochs: `3`
- Train batch size: `8`
- Evaluation batch size: `16`
- Gradient accumulation: `1` (one batch per optimizer update)
- Drop final partial batch: `false`
- Learning rate: `2e-5`
- Weight decay: `0.01`
- Class balancing: inverse-frequency weighted cross entropy
- Early stopping: validation macro-F1, patience `2`
- Precision: float32

One training step processes one batch and performs one optimizer update. With
104,045 training rows, batch size 8, and three epochs, the full run contains
39,018 optimizer steps.

## Execution and Reproducibility

### Local gates

Run before cloud training:

```bash
cd ml/nlp-workbench-latest
.venv/bin/python -m pytest -q tests
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

A bounded 5,000-row-per-split benchmark completed under run ID
`bert-benchmark-system12-high3-macbert-weighted-20260810-v1`. It reached
pseudo-label test macro-F1 `0.86877`; negative-class F1 was `0.71828`. These
numbers validate the selected weighted method only and are not the final
full-data result.

### Colab full run

Use the portable dataset-only boundary. Upload only the prepared Silver CSV and
minimum training code. Raw sources, historical latest files, and the current
backend matrix stay local.

```bash
python scripts/train_bert.py \
  --run-id bert-full-system12-high3-macbert-weighted-colab-20260810-v1 \
  --dataset output/runs/bert-prep-system12-high3-20260810-v1/bert/bert_pseudo_labeled_dataset.csv \
  --expected-dataset-sha256 64ff725a7f38696cb21a178249b3ce642c4f8bb99485a914b8beff80af89754d \
  --model-name hfl/chinese-macbert-base \
  --seed 42 \
  --max-length 128 \
  --epochs 3 \
  --train-batch-size 8 \
  --eval-batch-size 16
```

The run manifest must record:

```text
input_boundary.mode = portable_dataset_sha256
input_boundary.protected_source_assets_uploaded = false
promotion.status = not_promoted
gold_dataset_status = not_available
```

Before the Colab session is stopped, download the complete run directory to the
same local run ID and verify the dataset hash, metrics, predictions, tokenizer,
model weights, and manifests.

### Completed full-run evidence

Run ID:

```text
bert-full-system12-high3-macbert-weighted-colab-20260810-v1
```

The run completed all 39,018 optimiser steps and produced the following Silver
pseudo-label test metrics:

| Metric | Result |
| --- | ---: |
| Accuracy | `0.98819` |
| Macro-F1 | `0.97865` |
| Weighted-F1 | `0.98817` |
| Mention/non-mention F1 | `0.97990` |
| Negative-class F1 | `0.96582` |

The local artifact verification confirmed 33 expected files, including model
weights, tokenizer files, two retained checkpoints, predictions, metrics and
manifests. The frozen dataset SHA-256 matched the preparation run,
`input_boundary.mode=portable_dataset_sha256`, and
`promotion.status=not_promoted`. All 30 NLP tests passed before the Colab
session was stopped.

## Evaluation Claim Boundary

Report:

- accuracy
- macro-F1
- weighted-F1
- mention/non-mention F1
- per-class F1
- three-class confusion matrix
- split and per-label row counts

All current evaluation is against pseudo labels derived from the same rule
policy used to construct the Silver training data. The valid claim is:

> The model reproduces and generalizes the high-confidence Silver labeling
> policy on leakage-safe held-out partitions.

Do not claim that the metrics prove human sentiment accuracy or that MacBERT is
better than a human-validated baseline. Human Gold evaluation can be added as a
separate future research phase if two independent annotators and adjudication
become available.

## 12-by-9 Matrix Generation

After full training succeeds:

1. Run inference for the 12 approved strings and all nine aspects.
2. Retain class probabilities, predicted class, model run ID, and review/sample
   identifiers for audit.
3. Exclude low-confidence predictions from score aggregation rather than
   forcing every row into positive or negative evidence.
4. Aggregate positive and negative evidence by string and aspect.
5. Convert aggregate evidence to backend-compatible normalized scores,
   confidence, and review-count fields.
6. Preserve `attack` in the workbook; the backend maps the applicable attack
   signal into its runtime repulsion feature.
7. Write a versioned run-scoped CSV/XLSX. Do not write to the protected V9 path.

The output contains 12 rows and the nine domain aspects. Backend-derived fit
features may still be calculated by the existing importer/scorer; they are not
additional BERT labels.

## Feedback Linkage

The current application already persists one feedback record per completed
booking, including the selected `string_id`, free-text `string_feedback`, and
structured ratings.

Use the minimum batch flow:

```text
feedback export
  -> filter to the 12 approved strings
  -> create nine aspect-conditioned inputs per non-blank string comment
  -> MacBERT inference
  -> confidence-aware per-string aggregation
  -> versioned 12-by-9 matrix
  -> human-reviewed admin matrix import
```

Existing endpoints:

- `POST /api/bookings/{booking_id}/feedback`
- `GET /api/admin/feedback/export`
- `POST /api/admin/recommendation-matrix/import`

Structured comfort, control, repulsion, durability, and tension ratings can be
used as independent supporting evidence. They should not be silently replaced
by BERT predictions.

No inference is required inside the feedback request. Offline batch processing
is sufficient for the single-shop FYP scope and avoids keeping a large model in
the FastAPI runtime.

The feedback inference/aggregation script is not implemented yet. The offline
NLP operator owns export and inference; the shop admin/project owner reviews the
matrix and triggers import. Confidence thresholds, aggregation formula, and
score normalization must be fixed in the future inference task and recorded in
that run's manifest rather than inferred from this design.

## Promotion Gate

Training completion does not change the live system. Promotion requires a
separate explicit decision after:

1. Full run artifacts and hashes are verified locally.
2. Final pseudo-label metrics and class confusion are reviewed.
3. The generated 12-by-9 matrix matches all 12 approved catalog IDs.
4. Recommendation comparisons are run against the current V9 matrix using fixed
   player profiles.
5. The admin import reports no unmatched approved strings.
6. The current matrix is backed up and rollback remains available.

The FYP project owner is the promotion approver. No automatic numeric promotion
threshold has been approved yet; until one is recorded, the comparison evidence
supports a documented human decision rather than an automatic pass/fail.

### Approved promotion record

The project owner first instructed `我要替换掉V9`, then clarified
`新的bert matrix不要跟旧的V9合并一起` on 2026-08-12. The final promotion keeps
the reviewed `0.995` threshold and minimum evidence `20`, but stores the 108
MacBERT aspect cells in an independent workbook. The old V9 was restored to
SHA256 `382d71cd90e195fcc41550c38175c13e1bb01515615fda572cf22fee90e05209`.
The separate MacBERT Matrix SHA256 is
`dd30e792a213a03386101c4c8d6ba5aae07fa0bfc8d3f7439c6df92171424f87`.

## Done Criteria

- Full Colab model run completes and is downloaded under its immutable run ID.
- Model/tokenizer, metrics, predictions, manifests, and dataset hash verify.
- Experiment artifacts remain `not_promoted` until the promotion gate is
  approved; the separate promotion run records the approved transition.
- A repeatable inference script produces auditable predictions for nine aspects.
- A versioned 12-by-9 feature matrix is generated without changing protected
  current assets.
- Existing feedback export can feed the offline inference path.
- Existing backend importer accepts all 12 approved rows.
- Documentation keeps Silver, Gold, model, matrix, and runtime claims separate.
