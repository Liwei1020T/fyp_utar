# StringSense Proposal Notes: Silver-Supervised MacBERT Review Analysis

## Document Purpose

This document records the completed StringSense MacBERT experiment and the next
implementation phase. It is written as proposal-ready material, but it keeps a
strict distinction between completed evidence and planned work.

Status date: 12 August 2026.

## Current Status and Immediate Next Step

Offline inference, the 12-by-9 candidate Matrix, fixed-profile comparison and
owner review have completed. On 12 August 2026, the project owner clarified
that the new MacBERT Matrix must remain separate from the old V9 workbook.
Promotion run `bert-macbert-separate-matrix-promotion-20260812-v1` therefore
restored V9 unchanged and promoted a separate 12-string, 9-aspect MacBERT
workbook for the backend `nlp_review` source layer.

Docker/Postgres has recovered; migration `20260812_0028` is the codebase head, and the
canonical Matrix is imported as 108 `nlp_review` rows across the approved 12
strings with health status `imported`. No real-time inference or comment-POST
integration was introduced.

## 1. Research Background

Badminton-string reviews contain useful experience-based information about
performance characteristics, but the information is expressed as unstructured
text. A single review may discuss durability, hitting sound and tension
retention while saying nothing about other characteristics. Manually converting
all reviews into structured attributes would require substantial annotation
effort.

StringSense therefore investigates whether a domain-adapted language model can
learn a high-confidence rule-based Silver labelling policy and transform review
text into auditable item-side signals. The resulting signals are intended to
support string profiling and recommendation, not to replace the existing
backend scorer automatically.

## 2. Research Objective and Questions

The objective is to develop a reproducible aspect-conditioned classifier that
identifies whether a review contains positive evidence, negative evidence or no
evidence for a specified badminton-string characteristic.

The study addresses three questions:

1. Can high-confidence Silver labels train MacBERT to reproduce the domain
   labelling policy on leakage-safe held-out data?
2. Can one bounded model support nine characteristics across the 12 strings
   available in the StringSense system?
3. Can model outputs be converted into reviewable recommendation features
   without introducing a real-time AI service or automatic model promotion?

## 3. Scope and Claim Boundary

### Included scope

- 12 system-approved badminton strings
- nine review aspects
- three labels: `not_mentioned`, `positive` and `negative`
- high-confidence rule-based Silver supervision
- `hfl/chinese-macbert-base` as the primary model
- leakage-safe train, validation and test partitions
- offline training and offline batch inference

### Excluded scope

- human Gold labels or human-ground-truth accuracy claims
- independent annotator agreement or Cohen's Kappa
- zero-shot natural language inference
- five-class classification
- training or deployment for all 33 historical source strings
- synchronous model inference inside the comment submission request
- automatic retraining from new comments
- automatic replacement of the current recommendation matrix

The current evaluation measures agreement with held-out Silver pseudo labels.
It does not prove that the classifier is 98.82% accurate against independent
human judgement.

## 4. System Cohort and Aspects

The active cohort is restricted to:

1. Yonex BG80
2. Yonex BG65
3. Yonex BG66 ULTIMAX
4. Yonex BG80 POWER
5. Yonex EXBOLT 63
6. Yonex AEROBITE
7. Victor VBS-66 NANO
8. Victor VBS-68 Power
9. Li-Ning No.1
10. Li-Ning N65
11. Gosen RYZONIC 65
12. Kumpoo JS-63

The nine aspects are `attack`, `comfort`, `control`, `durability`, `elasticity`,
`sound`, `string_movement`, `tension_retention` and `value_for_money`.

For each review-aspect pair, the model receives an input in this form:

```text
目标球线：<canonical string name>
评价方面：<Chinese aspect description>
评论：<review text>
```

The output is one of the three approved labels. Running the model once per
aspect produces a nine-part feature interpretation for one comment.

## 5. Dataset Preparation

The prepared dataset is stored under the immutable run ID
`bert-prep-system12-high3-20260810-v1`.

| Field | Value |
| --- | ---: |
| Approved strings | 12 |
| Source reviews in the cohort | 16,184 |
| Review-aspect rows | 130,421 |
| Training rows | 104,045 |
| Validation rows | 13,077 |
| Test rows | 13,299 |
| `not_mentioned` rows | 95,455 |
| `positive` rows | 28,127 |
| `negative` rows | 6,839 |

Frozen dataset SHA-256:

```text
64ff725a7f38696cb21a178249b3ce642c4f8bb99485a914b8beff80af89754d
```

All aspects from the same review and all duplicate normalized texts inherit one
partition. The preparation report records zero review, normalized-text or split
group crossings. Every training row retains the provenance
`rule_based_silver_not_human_gold`.

The raw JSON, historical `*_latest.csv` files and current backend workbook were
not overwritten.

## 6. Model and Training Configuration

| Configuration | Value |
| --- | --- |
| Primary model | `hfl/chinese-macbert-base` |
| Task | Aspect-conditioned three-class sequence classification |
| Random seed | 42 |
| Maximum sequence length | 128 |
| Epochs | 3 |
| Training batch size | 8 |
| Evaluation batch size | 16 |
| Learning rate | `2e-5` |
| Weight decay | `0.01` |
| Class balancing | Inverse-frequency weighted cross entropy |
| Early stopping metric | Validation macro-F1 |
| Precision | Float32 |
| Training hardware | Google Colab Tesla T4 |

Training completed 39,018 optimiser steps in approximately 6,949.70 seconds
(1 hour 55 minutes 50 seconds). The portable Colab boundary uploaded only the
prepared dataset and minimum training code. Protected raw inputs and the active
backend matrix remained local.

## 7. Completed Evaluation

The completed run is
`bert-full-system12-high3-macbert-weighted-colab-20260810-v1`.

### Silver pseudo-label test metrics

| Metric | Result |
| --- | ---: |
| Accuracy | 0.98819 |
| Macro-F1 | 0.97865 |
| Weighted-F1 | 0.98817 |
| Mention/non-mention F1 | 0.97990 |
| `not_mentioned` F1 | 0.99287 |
| `positive` F1 | 0.97728 |
| `negative` F1 | 0.96582 |

### Confusion matrix

Rows are true Silver labels and columns are predicted labels.

| True label | Predicted `not_mentioned` | Predicted `positive` | Predicted `negative` |
| --- | ---: | ---: | ---: |
| `not_mentioned` | 9,747 | 57 | 4 |
| `positive` | 53 | 2,731 | 5 |
| `negative` | 26 | 12 | 664 |

The result supports the claim that MacBERT reproduces and generalises the
high-confidence Silver labelling policy on leakage-safe held-out partitions.
The result must be reported as `pseudo_label_validation_only`, not as human
sentiment accuracy.

## 8. Proposed System Use

The trained classifier can support four bounded functions:

1. classify a comment for each of the nine aspects;
2. show positive and negative characteristic tags for a string;
3. aggregate accepted evidence into a per-string characteristic profile; and
4. supply item-side features to the existing recommendation workflow.

The proposed data flow is:

```text
Persisted string comments
  -> select comments for the 12 approved strings
  -> generate nine aspect-conditioned inputs per comment
  -> run offline MacBERT inference
  -> retain predictions, probabilities and provenance
  -> exclude low-confidence evidence
  -> aggregate a versioned 12-by-9 matrix
  -> review the matrix
  -> import only after explicit approval
```

The comment submission API should continue saving feedback normally. Model
inference should initially run as a separate batch or admin-triggered operation,
so model latency or failure cannot block users from submitting comments.

## 9. Proposed Scoring Method for the Pilot

For each string and aspect, retain only accepted `positive` and `negative`
predictions. A simple pilot score can be calculated as:

```text
positive_weight = sum(confidence for accepted positive predictions)
negative_weight = sum(confidence for accepted negative predictions)
positive_share = positive_weight / (positive_weight + negative_weight)
score_1_to_5 = 1 + (4 * positive_share)
```

`not_mentioned` predictions should affect coverage reporting but not sentiment
direction. Each matrix cell should also store accepted evidence count, total
comment count, coverage, model run ID and generation timestamp.

The inference confidence threshold and minimum evidence count are not final
research results. They must be selected during the next acceptance exercise. A
cell with insufficient evidence should remain unavailable or fall back to the
existing approved feature value rather than presenting a misleading score.

## 10. Next Phase Work Packages

### WP1 — Offline inference command

Implement one run-scoped command that loads the downloaded model and produces
predicted label plus all three class probabilities. It must accept the canonical
string name, aspect and review text and must reject strings outside the approved
cohort.

### WP2 — Small manual acceptance exercise

Select a balanced, traceable sample of comments from the 12 strings and inspect
the nine-aspect predictions. This is an operational error-analysis exercise,
not a Gold dataset and not Cohen's Kappa. Record obvious false positives, false
negatives, comparison-text errors and negation errors.

### WP3 — Confidence and evidence gate

Compare a small set of candidate confidence thresholds using error patterns and
coverage. Select one pilot threshold and a minimum evidence count. Record the
decision rather than tuning it silently.

### WP4 — Versioned 12-by-9 matrix

Aggregate accepted predictions using the pilot scoring method. Write CSV/XLSX
and evidence files only under a new `output/runs/<run-id>/` directory. Do not
overwrite `output/latest_practical_string_feature_matrix_v9_v8dict.xlsx`.

### WP5 — Backend preview and approval

Use the existing recommendation-matrix import path to preview the new values.
Compare recommendation behaviour before and after import. Promotion remains a
separate, explicit approval action.

### WP6 — Comment linkage

After the offline matrix is accepted, add a batch or admin-triggered path that
processes newly persisted comments and regenerates a new versioned matrix. Do
not place MacBERT inference inside the synchronous comment POST request in the
first implementation.

## 11. Definition of Done for the Offline Candidate Phase

The offline candidate phase was complete when:

- inference is deterministic for the same model, input and seed;
- only the 12 approved strings and nine approved aspects are accepted;
- every prediction records the model run ID and class probabilities;
- low-confidence and insufficient-evidence cases remain visible and excluded;
- a new run-scoped 12-by-9 matrix and its evidence file are generated;
- the protected V9 workbook remained unchanged before separate promotion;
- relevant NLP tests pass;
- the candidate output remained `promotion.status=not_promoted`; and
- a human-readable comparison report is available before any backend import.

## 12. Limitations and Future Work

The primary limitation is the absence of independent human Gold labels. The
model may learn systematic errors present in the Silver rules, and a high
Silver test score can therefore overstate real semantic quality. Softmax output
is also not automatically a calibrated probability of correctness.

If time and annotator resources become available, a future study may create a
small independently annotated Gold test set, calculate inter-annotator
agreement, adjudicate disagreements and evaluate the frozen model without
retraining on that Gold test set. This would strengthen the validity claim but
is not required for the current bounded FYP implementation.

The current model is intentionally limited to the 12 system strings. Supporting
new products would require data sufficiency checks, canonical-name updates and
a new versioned experiment rather than silently treating the present model as
open-domain.

## 13. Proposal-Ready Summary Paragraph

> This study develops an aspect-conditioned MacBERT classifier for extracting
> structured badminton-string characteristics from user reviews. The model is
> trained on 130,421 high-confidence Silver review-aspect instances covering 12
> system-approved strings and nine domain aspects. A leakage-safe grouped split
> is used to prevent the same review or duplicate normalised text from crossing
> training, validation and test partitions. On the held-out Silver test set,
> the classifier achieves 0.98819 accuracy and 0.97865 macro-F1. These results
> demonstrate reproduction of the Silver labelling policy rather than
> human-ground-truth accuracy. A subsequent offline aggregation phase
> generated and reviewed a 12-by-9 feature matrix. After fixed-profile review,
> the project owner approved a separate MacBERT Matrix and explicitly rejected
> merging it into V9; official performance and user preferences remain separate
> scoring inputs.

## 14. Reproducibility Evidence

- Full run manifest:
  [`run_manifest.json`](../ml/nlp-workbench-latest/output/runs/bert-full-system12-high3-macbert-weighted-colab-20260810-v1/run_manifest.json)
- Final metrics:
  [`training_metrics.json`](../ml/nlp-workbench-latest/output/runs/bert-full-system12-high3-macbert-weighted-colab-20260810-v1/bert_training/training_metrics.json)
- Test predictions:
  [`test_predictions.csv`](../ml/nlp-workbench-latest/output/runs/bert-full-system12-high3-macbert-weighted-colab-20260810-v1/bert_training/test_predictions.csv)
- Model weights:
  [`model.safetensors`](../ml/nlp-workbench-latest/output/runs/bert-full-system12-high3-macbert-weighted-colab-20260810-v1/bert_training/model/model.safetensors)
- Detailed design record:
  [`BERT ABSA Review Optimization Design`](../docs/superpowers/specs/2026-05-31-bert-absa-review-optimization-design.md)

The downloaded run contains 33 expected files and 2,866,662,469 bytes of model,
checkpoint and evidence data. Its manifest records
`input_boundary.mode=portable_dataset_sha256`,
`protected_source_assets_uploaded=false`, `gold_dataset_status=not_available`
and `promotion.status=not_promoted`. Local NLP validation completed with 30
passing tests before the Colab session was stopped.

The superseded merged promotion remains recorded under
`bert-macbert-v9-promotion-20260812-v1`. The current separate-Matrix decision
is recorded under `bert-macbert-separate-matrix-promotion-20260812-v1`; neither
record mutates the immutable training run's original `not_promoted` status.
