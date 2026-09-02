# Racket-Conditioned Collaborative Recommendation Design

> Current-runtime note: this design records the V11 CF policy and its original
> V13 activation. The active scorer is now V14; see
> [`backend/docs/recommendation-design.md`](../../../backend/docs/recommendation-design.md)
> for the current ranking contract.

## Document Status

| Field | Value |
| --- | --- |
| Status | V11 CF policy retained inside active V14 scoring; production evidence remains separate |
| Last reviewed | 2026-09-02 |
| Runtime cohort | `config/approved_string_cohort_v1.csv` (12 strings) |
| Baseline algorithm | `fyp1_similarity_preferences_v9` |
| Historical feedback comparison algorithm | `fyp1_similarity_preferences_feedback_v10` |
| Active scoring algorithm | `fyp1_weighted_preferences_feedback_racket_cf_personal_v14` |
| Current CF status | Guarded enablement above three exact-model supporting users |
| Implementation status | Scoring, fallback, audit, cache versioning, and demo evaluation implemented |
| Racket similarity status | Exact normalized model matching active; fuzzy cross-model similarity is an explicit non-goal |
| Racket identity input | Authenticated six-model server catalogue and mobile selector implemented; `Other model` is global-only |
| CF weight status | Automatically recalculated from distinct supporting users; automatic policy tuning deferred |

This document replaces the earlier design in which racket similarity was only a
final-score bonus. The recommendation context is the selected racket, and the
behavioral observation is a completed racket-string-tension interaction.

V11 implementation and guarded FYP-demo activation are recorded separately from
production readiness. This design does not authorize production data changes or
claim that the current real-user dataset is sufficient for production-quality
collaborative-filtering effectiveness.

## Decision Summary

StringSence will use a hybrid recommendation architecture:

```text
Racket-conditioned hybrid recommendation =
  stable content/rule baseline
+ structured feedback outcome calibration
+ racket-conditioned collaborative support
+ tension-context fit
+ exact cold-start fallback
```

The important separation is:

- a completed booking means that a player used a string on a racket; it is an
  implicit interaction, not proof of satisfaction;
- structured booking feedback describes the observed result of that
  racket-string combination;
- collaborative filtering learns behavioral support from similar users and
  completed interactions;
- MacBERT continues supplying offline review-derived string features and is not
  the collaborative-filtering model.

The first implementation uses the existing PostgreSQL data, scorer, cache, and
recommendation-run audit. It does not add neural CF, a vector database, a model
service, a job queue, or a new racket metadata service.

## Why Racket Is Part of the Context

The same string can produce different comfort, control, repulsion, durability,
and tension satisfaction when installed on different rackets or at different
tensions. Therefore this design must answer:

> For this player, this selected racket, and this target tension, which approved
> string has the strongest supported result?

It must not reduce the question to:

> Which string is generally popular?

Racket brand alone is not a performance category, and similar-looking model
names do not prove physical similarity. Text normalization may reconcile
capitalization, punctuation, and whitespace, but fuzzy model-name similarity
must not be used as evidence that two rackets behave alike.

## Current System Evidence

### Existing usable data path

`bookings` already stores:

```text
user_id
string_id
racket_id (nullable)
racket_brand snapshot
racket_model snapshot
requested_tension
status
status history
```

When a saved racket is selected during booking creation, the backend validates
ownership and copies its brand/model into the booking. The copied booking fields
are the historical identity snapshot; later edits to the saved racket must not
rewrite past interactions.

`booking_feedback` already stores structured outcome fields including comfort,
control, repulsion, durability, string satisfaction, tension satisfaction, and
whether the player would use the string again. Their eligibility and provenance
rules are owned by
`2026-08-11-feedback-calibration-design.md`.

### Runtime wiring implemented

The recommendation request accepts an owned `racket_id`. The backend resolves
and snapshots its normalized brand/model context, and the mobile recommendation
screen lets the player select a saved racket. The current scorer records either:

```text
collaborative_filtering_used = true   when a non-zero gated CF weight is applied
collaborative_filtering_used = false  for profile-only or sparse fallback
```

Persisted recommendation evidence includes the raw CF score, distinct supporting
users, automatically calculated weight, source version, and fallback reason.

Racket Passport create/edit now obtains the six FYP standard models from the
authenticated `GET /api/racket-models` endpoint and submits the selected
server-owned `model_key`. The backend rejects unknown keys and replaces any
client-supplied brand/model display text with the canonical catalogue values.
Legacy exact text is canonicalized for compatibility. A custom `Other model`
remains valid, but its key is `null`: its feedback contributes globally and its
cross-user CF weight stays zero instead of guessing a similar model.

### Standard identity acceptance evidence (2026-08-13)

- the authenticated catalogue returned six unique standard keys;
- a real Expo Web player flow created `Yonex Astrox 88D Pro`, reopened its edit
  form, and exposed `Other model` inputs only after that option was selected;
- a second PostgreSQL user submitted the same key with spoofed display text and
  the backend stored the canonical `Yonex / Astrox 88D Pro` identity;
- both distinct users received `yonex:astrox 88d pro` in V11 rationale;
- with the same profile and 26 lbs target, both users received the same top-three
  order (`yonex-exbolt-63`, `kumpoo-js-63`, `gosen-ryzonic-65`);
- current candidate support remained below the three-user gate, so both runs
  truthfully recorded `cf_weight=0` and
  `insufficient_distinct_supporting_users` instead of claiming learned accuracy;
- an unknown submitted `model_key` returned HTTP 400.

This evidence proves deterministic identity and fallback behaviour. It does not
claim production CF accuracy; that still requires enough independent completed
interactions per exact model/string candidate.

### Historical pre-V11 data sufficiency snapshot

Before the labelled FYP demo interaction import on 2026-08-13, the approved
cohort had:

| Signal | Count |
| --- | ---: |
| Completed bookings | 5 |
| Completed bookings linked to a saved `racket_id` | 1 |
| Distinct normalized racket models | 2 |
| Distinct racket-model/string pairs | 3 |
| Completed rows with tension | 5 |
| Feedback rows for those completed bookings | 1 |

That historical snapshot justified deterministic aggregation, cold-start
fallback, audit evidence, and guarded scoring. The later labelled synthetic demo
dataset may activate the gate for demonstration, but it is still not evidence
that a stable cross-user relationship has been learned from real usage.

## Terminology and Identity

| Term | Meaning |
| --- | --- |
| Physical racket | One saved racket owned by a player, identified by `racket_id` |
| Racket model key | Normalized booking snapshot of `racket_brand + racket_model` |
| Interaction | One approved-string booking that reached `completed` |
| Target context | Selected racket model and requested/preferred tension for this recommendation |
| Behavioral support | Evidence from completed interactions; not a satisfaction claim |
| Outcome evidence | Eligible structured feedback for a completed interaction |
| Cold-start fallback | Exact previous algorithm behavior when contextual evidence is insufficient |

Normalization uses only deterministic standard-library operations:

```text
Unicode normalize -> casefold -> trim -> collapse punctuation/whitespace
```

It may make `Astrox 88D Pro` and `ASTROX-88D PRO` the same key. It must not infer
that `Astrox 88D` and `Astrox 88D Pro`, or two rackets from the same brand, are
physically equivalent.

## Target Request Flow

The authenticated profile recommendation accepts a selected saved racket:

```http
POST /api/recommendations/profile
Content-Type: application/json

{
  "top_n": 3,
  "racket_id": "owned-racket-id"
}
```

Rules:

1. `racket_id` is optional for backward-compatible cold start.
2. When supplied, the backend verifies that the racket belongs to the current
   player and resolves its current identity for the target context.
3. The request snapshot records `racket_id`, brand, model, normalized model key,
   and target tension.
4. Mobile asks the player to select one saved racket before generating a
   racket-aware recommendation. If none is selected, it labels the result as
   profile-based and does not claim racket-aware learning.
5. The selected racket is carried into booking creation so later completed
   interaction and feedback evidence remains traceable.

The simplest cache behavior is one latest shortlist per user and algorithm.
Generating v11 for another racket replaces that user's previous v11 cache rows,
while immutable recommendation runs retain every historical context. A new cache
key or multi-racket cache table is unnecessary unless the product later needs
simultaneous saved shortlists for multiple rackets.

## Eligible Interaction Data

A CF interaction is eligible only when:

- `booking.status = completed`;
- `string_id` is in the approved 12-string cohort;
- `racket_brand` and `racket_model` snapshots produce a non-empty model key;
- the completed status-history timestamp exists;
- the booking belongs to a real authenticated customer.

Cancelled, rejected, awaiting-dropoff, in-progress, and ready-for-collection
bookings are excluded.

`requested_tension` is contextual when present. Missing tension does not erase
the interaction, but that row receives no tension-similarity support.

Repeated completed bookings remain separate raw events, but aggregation first
reduces them to one contribution per:

```text
user_id + racket_model_key + string_id
```

This prevents one frequent customer from dominating a racket-string pair.

## Evidence Hierarchy

The system uses the most specific valid evidence and falls back safely:

1. the current player's history for the exact physical `racket_id`;
2. cross-user history for the exact normalized racket model;
3. global approved-string feedback evidence;
4. the stable content/rule baseline.

Same-brand-only and fuzzy-model matches are not evidence tiers in v1. Racket
attributes such as weight class and balance point may support a future physical
similarity tier only after those values are complete, historically snapshotted,
and validated.

## Collaborative Filtering

### Model position

The first model is classical, context-aware user-neighborhood CF. The recommended
thesis wording is:

> The recommendation module combines content-based and rule-based scoring with
> racket-conditioned user-neighborhood collaborative filtering derived from
> completed racket-string interactions among players with similar preferences.

The candidate item remains the string. Racket model and tension are interaction
contexts; they are not independent popularity bonuses.

### User similarity

Reuse the current persisted preference vector and profile fields. Similarity may
use cosine similarity for the nine preference dimensions, with exact categorical
matches for playing style and skill level. Missing fields contribute no support;
they are not converted to zero preference.

Do not reintroduce removed request fields such as `budget_tier`.

### Racket-conditioned support

For current user `u`, exact target racket model `r`, candidate string `s`, and
target tension `t`, build a peer pool from other users with at least one eligible
completed interaction on `r`.

For each peer, first reduce repeated bookings of the same `r + s` to one
per-user contribution. Then calculate:

```text
peer_weight(v) = preference_similarity(u, v)

candidate_support(v, r, s, t) =
  peer_weight(v)
  * average_tension_similarity(v's completed r + s interactions, t)

racket_conditioned_cf_score(r, s) =
  sum(candidate_support for peers who completed r + s)
  / sum(peer_weight for every eligible peer in racket-model r)
```

Only exact normalized racket-model interactions enter cross-user support in v1.
The current user is excluded from the peer pool. Their exact physical-racket
history remains audit and outcome context; it is not an automatic positive boost
because prior completion alone does not prove satisfaction.

Tension similarity is continuous rather than an exact bucket:

```text
tension_similarity =
  max(0, 1 - abs(target_tension - observed_tension)
               / TENSION_SIMILARITY_WINDOW_LBS)
```

`TENSION_SIMILARITY_WINDOW_LBS` is one reviewable policy constant. V11 uses
`4.0` for guarded FYP-demo evaluation; do not present it as a scientific
threshold.

An interaction without requested tension remains visible in general history but
does not contribute to the tension-conditioned CF numerator. If all candidate or
peer support is missing tension, CF falls back with zero weight.

### Completed is not positive satisfaction

A completed booking contributes behavioral support only. It must not be mapped
to a five-star outcome or a positive feature score.

Structured feedback owns outcome learning:

- performance ratings calibrate the feature evidence for the applicable
  racket-string context;
- `string_satisfaction`, `tension_satisfaction`, and `would_use_again` remain
  outcome/audit metrics until a separately reviewed scalar-utility rule exists;
- service rating, comments, tags, usernames, and phone numbers never enter CF.

This prevents the same feedback row from being converted into several invented
positive interactions.

## Combining Feedback and CF

The two proposals are one delivery programme but separate signals:

```text
v9 baseline
  -> v10 structured feedback calibration
  -> v11 racket-conditioned CF blend
```

For a selected racket, the feedback module returns contextual feature evidence
using the exact racket-model/string pair when valid; otherwise it falls back to
the global string aggregate and then the v9 feature baseline.

The CF layer then supplies behavioral support from completed interactions. It
does not read raw feedback fields and does not recalibrate features a second
time.

This separation allows three comparisons:

1. v9 content/rules only;
2. v10 content/rules plus structured outcomes;
3. v11 v10 base plus racket-conditioned CF.

It also makes rollback and thesis evaluation attributable. Developing both in
one project does not require enabling both in one unreviewed release.

## Score Blending and Confidence

The stable base score remains v10 when feedback calibration is enabled, or v9
when it is not.

```text
cf_confidence = distinct_supporting_users
                / (distinct_supporting_users + CF_SHRINKAGE_K)

cf_weight = CF_MAX_WEIGHT * cf_confidence

final_score = base_score * (1 - cf_weight)
            + racket_conditioned_cf_score * cf_weight
```

Guarded V11 demo policy:

```text
CF_SHRINKAGE_K = 10
CF_MAX_WEIGHT = 0.20
TENSION_SIMILARITY_WINDOW_LBS = 4.0
```

These remain calibration knobs rather than scientific constants. Demo evaluation
and every immutable run must expose their resulting weight and ranking effect.

CF influence is zero when:

- no racket is selected;
- the target racket model is incomplete;
- no eligible exact-model neighbors exist;
- the computed support denominator is zero;
- candidate support is below three distinct users.

When CF influence is zero, output ordering and scores must exactly equal the
selected base algorithm. Do not add a neutral `0.5` score and accidentally
change the ranking.

## Audit Evidence

Recommendation rationale and admin audit record:

```text
racket_context
  racket_id
  brand
  model
  normalized_model_key
  target_tension

cf_evidence
  mode: unavailable | fallback | shadow | enabled
  distinct_supporting_users
  completed_interaction_count
  physical_racket_history_count
  exact_model_match_count
  tension_supported_count
  raw_cf_score
  cf_confidence
  cf_weight
  base_score
  final_score
  fallback_reason
  policy_version
  source_version
```

`collaborative_filtering_used` is true only when a non-zero CF weight changes the
enabled final score. Shadow computation remains false and records
`mode = shadow`.

Player wording stays factual. For example:

> This result considers your selected Yonex Astrox 88D Pro, preferred tension,
> saved preferences, and available completed-booking patterns.

Do not claim “players with this racket preferred this string” unless the audit
has eligible cross-user support.

## Source Version and Cache Invalidation

Generate a deterministic CF source version from:

- CF policy version and approved cohort version;
- eligible booking ID;
- user ID hashed only inside the server-side digest input;
- string ID;
- normalized racket-model key;
- requested tension;
- completed status-history timestamp.

Sort canonical rows before SHA-256 hashing. Do not include comments, service
feedback, phone numbers, usernames, mutable booking `updated_at`, or current
racket-table text.

When an eligible booking becomes completed or an already-completed booking's
eligible context is corrected, invalidate v11 caches transactionally. Immutable
runs and logs remain unchanged.

Feedback cache invalidation remains governed by the feedback-calibration source
version. A v11 cached result is current only when both its feedback snapshot and
CF source version match the latest values.

## Shadow Evaluation and Activation Gate

The original database was too sparse for enabled CF. V11 is now guarded:

1. calculate CF evidence and persist it in the immutable run rationale;
2. enable weight only from three independent exact-model supporters;
3. retain exact v10 scores for sparse candidates and profile-only runs;
4. evaluate labelled demo fixtures separately from real usage;
5. never inject synthetic interactions into runtime analytics.

Synthetic, explicitly labelled fixtures may be used for deterministic tests and
an isolated demonstration dataset. They are not evidence of real-user model
quality.

Production-quality claims still require all of the following:

- at least three distinct supporting users for an affected exact racket-model
  context;
- enough historical rows to produce at least 20 leave-one-out evaluation cases;
- no regression in cold-start availability;
- reviewed Top-K hit-rate and ranking-delta results against the same frozen base;
- complete audit evidence and exact fallback tests;
- explicit owner approval of policy constants and enabled algorithm version.

These are conservative operational gates, not claims of statistical
significance. If real usage remains sparse, v11 returns the exact v10 base score
for unsupported candidates.

## Implementation Record

### Phase 1: Add target-racket context without changing ranking — completed

- `ProfileRecommendationPayload` accepts optional `racket_id`;
- the use case validates ownership and resolves target context;
- mobile lets the player select a saved racket on the recommendation screen;
- request/profile snapshots and rationale persist the context;
- profile-only fallback preserves exact base behavior.

### Phase 2: Build the read-only CF aggregate — completed

- one booking-backed repository query loads eligible completed interactions;
- one shared function normalizes racket-model keys;
- aggregation calculates per-user deduplicated support, tension similarity,
  confidence, and source version;
- complete audit evidence is written before any gated score change;
- the admin readiness summary is available.

Do not add a new persisted interaction table; existing bookings are the source of
truth at the current scale.

### Phase 3: Integrate contextual feedback outcomes — completed

The corrected form, provenance, context aggregate, and cache policy are
integrated. CF reads only completed-booking interactions, and feedback changes
feature outcome evidence only once.

### Phase 4: Evaluate and guard-enable V11 — completed for FYP demo

- v9, v10, and v11 are distinguishable on the same frozen cases;
- real and labelled-fixture results remain separate;
- demo metrics are labelled synthetic and production claims remain gated;
- `fyp1_similarity_preferences_feedback_racket_cf_v11` records non-zero CF
  influence only when the support gate is met.

## Focused Test Plan

1. A recommendation cannot use another player's `racket_id`.
2. No selected racket returns the exact base ordering and scores.
3. Every standard catalogue key matches the normalized canonical brand/model.
4. Unknown keys are rejected; custom and fuzzy model text contributes globally
   but never creates cross-model CF support.
5. Only approved completed bookings enter CF.
6. Repeat interactions from one user are reduced before cross-user support.
7. A completed booking is never converted into a satisfaction rating.
8. Exact physical-racket history and exact model cross-user history remain
   distinguishable in evidence.
9. Missing tension contributes no tension similarity and does not crash scoring.
10. Zero CF support produces zero weight, not a neutral synthetic score.
11. Below-gate evidence records fallback details and does not alter ranking.
12. Source hashing is deterministic and ignores mutable/PII fields.
13. Completing an eligible booking invalidates v11 cache without changing runs.
14. A feedback update changes contextual outcome evidence but does not create a
    second CF interaction.
15. Mobile visibly distinguishes racket-aware and profile-only recommendations.
16. PostgreSQL, backend, mobile typecheck, lint, and targeted flow tests pass.

## Acceptance Criteria

- [x] The recommendation request identifies the selected owned racket.
- [x] Standard Racket Passports use a server-validated catalogue key across
      different users and clients.
- [x] Custom `Other model` rackets remain usable through exact base/global
      fallback with no inferred CF neighbor.
- [x] Every racket-aware result records an immutable racket context snapshot.
- [x] CF interactions are approved completed bookings only.
- [x] The model learns exact racket-model/string behavior; it does not infer
      physical similarity from brand or fuzzy text.
- [x] Tension affects context through a reviewable continuous policy.
- [x] Structured feedback represents outcome; completion represents use.
- [x] Feedback evidence is not double-counted in the CF term.
- [x] Repeated users cannot dominate a pair.
- [x] Sparse evidence returns exact base behavior.
- [x] Sparse data keeps the exact v10 base score through a zero-weight fallback.
- [x] Player and admin explanations match actual evidence.
- [x] v9, v10, and v11 runs remain distinguishable and reproducible.
- [x] FYP demo activation uses labelled synthetic evaluation separated from
      production-quality claims.

## Explicit Non-Goal

Fuzzy physical-racket or learned cross-model similarity is not planned for the
FYP. Exact normalized brand/model matching is the final supported racket identity
tier and this item must not be reported as unfinished work.

## Deferred Work

- learned racket embeddings or neural collaborative filtering;
- a full manufacturer racket-specification database;
- persisted aggregate/materialized-view tables;
- simultaneous cached shortlists for several rackets;
- automated tuning of `CF_MIN_SUPPORTING_USERS`, `CF_SHRINKAGE_K`, or
  `CF_MAX_WEIGHT`; runtime candidate weight is already recalculated
  automatically from the current distinct supporting-user count;
- treating free-text feedback as model input.

Add them only when real data volume and measured quality show that the simpler
exact-model, shadow-first design is insufficient.

## Decisions Applied to V11

1. Saved-racket selection is required for claiming a
   racket-aware recommendation.
2. Exact normalized brand/model matching is the only cross-user racket
   identity tier in v1.
3. Only the six server-catalogued FYP models receive a cross-user key; custom
   rackets use global feedback evidence and zero CF weight.
4. V11 uses `CF_MIN_SUPPORTING_USERS=3`, `CF_SHRINKAGE_K=10`,
   `CF_MAX_WEIGHT=0.20`, and a 4 lb tension window as reviewable demo policy.
5. The activation gate keeps real-data metrics separate from
   labelled test/demo fixtures.
6. Algorithm versions remain staged: v10 outcome calibration, then v11 enabled
   racket-conditioned CF.
