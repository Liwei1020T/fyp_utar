# String catalog data audit — 2026-08-17

The seeded database was checked after loading the current catalog source and
the approved 12-string cohort.

| Check | Result |
| --- | --- |
| Active approved strings | 12 |
| Catalog source URLs | 12/12 |
| Gauge metadata | 12/12 |
| Material metadata | 12/12 |
| Official-performance source URLs | 0/12 |
| Official-performance status | 12/12 `pending_manual_fill` |
| Populated performance dimensions | 12/12 have `feel` only |

The catalog has descriptive and structured product metadata, but it does not
yet contain source-backed official performance ratings. The populated `feel`
values come from the bounded seed map in
`backend/app/adapters/persistence/sqlalchemy/catalog_seed.py`; they must not be
presented as manufacturer ratings. Recommendation/NLP/community values remain
separate evidence layers.

The audit also found duplicated punctuation in generated descriptions. Migration
`20260817_0031` repairs existing rows, and the seed normalizer prevents the same
`..` text from returning on a fresh database.
