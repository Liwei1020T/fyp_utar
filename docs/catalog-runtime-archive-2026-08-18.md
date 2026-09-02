# Runtime Catalog Archive — 2026-08-18

> Historical snapshot. This archive describes the pre-`20260902_0042` runtime
> and is superseded by the current 12-string seed and database schema. Do not
> use it as the current runtime state.

## Result

The retained PostgreSQL runtime keeps 33 catalog records for referential and
research provenance, but only the approved 12 are active. The other 21 catalog
and inventory records are inactive, and every archived inventory row is marked
`out_of_stock`.

Historical bookings and saved recommendation runs were preserved. Six bookings
refer to four archived strings, so physically deleting all 21 catalog rows would
break business-history integrity.

## Recovery Evidence

Private, Git-ignored recovery files:

- `backend/var/backups/stringsense-pre-12-only-20260818T142221.dump`
- `backend/var/backups/stringsense-pre-12-only-20260818T142221.dump.sha256`
- `backend/var/backups/nonapproved-string-state-20260818T142221.csv`
- `backend/var/backups/nonapproved-string-state-20260818T142221.csv.sha256`

The custom-format dump was restored into a temporary PostgreSQL database before
the archive transaction. The restored copy contained Alembic head
`20260818_0032`, 33 strings, and 377 bookings. The temporary verification
database was removed afterward.

These files contain private runtime data and must not be committed or shared.

## Restore One Archived String

1. Add the catalog ID to `config/approved_string_cohort_v1.csv` through an
   explicitly approved cohort change.
2. Read the string's prior activation, availability, stock, and pricing values
   from `nonapproved-string-state-20260818T142221.csv`.
3. In one PostgreSQL transaction, set `strings.is_active = true` and restore the
   matching `inventory_items` activation and availability values.
4. Restart the backend and run `backend/tests/test_system_string_cohort.py`.
5. Verify the catalog API, inventory API, booking selection, and recommendation
   candidates before treating the string as restored.

Do not reactivate only the database row without changing the approved cohort;
the cohort is the runtime authorization boundary shared by the backend and NLP.

## Full Disaster Recovery

Restore the dump into a separate database first. Do not overwrite the live
database. Verify the `.sha256` sidecar, inspect the restored catalog rows, then
copy only the approved recovery scope into the live database.
