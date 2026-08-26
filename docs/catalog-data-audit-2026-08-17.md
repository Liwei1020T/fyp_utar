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
| Official-performance status | 12/12 `manual_reviewed` |
| Populated performance dimensions | 12/12 have all six runtime dimensions |

The approved cohort now contains the manually reviewed official performance
values in the canonical seed source
`backend/data/string_catalog_db_ready.json`. The runtime seed preserves the
source metadata and six performance dimensions without reintroducing the
removed official-performance `source_url` field. Recommendation/NLP/community
values remain separate evidence layers.

The audit also found duplicated punctuation in generated descriptions. Migration
`20260817_0031` repairs existing rows, and the seed normalizer prevents the same
`..` text from returning on a fresh database.
