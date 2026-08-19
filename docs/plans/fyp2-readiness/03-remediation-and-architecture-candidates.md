# StringSence FYP2 Readiness — Architecture Candidates and Gates

> Historical implementation plan. The selected `F -> A -> C -> B -> D -> E`
> sequence and its verification results are recorded in
> [04-remediation-results-and-readiness.md](04-remediation-results-and-readiness.md).

## Constraint

This is a discussion document, not an implementation design. It names the
Modules and Seams that should become deeper, but deliberately does not prescribe
exact Interfaces, classes, endpoints or schema changes before the user chooses
the candidates and order.

No candidate is approved merely because it appears below.

## Architecture assessment

StringSence already has useful high-level separation between `mobile`,
`backend`, and the offline canonical NLP workbench. The main weakness is not a
lack of folders; it is that important domain decisions live in shallow or
duplicated Implementations:

- booking availability is displayed by one path but not enforced by the write
  path;
- catalog, visibility and stock are coupled through convenience updates;
- Mobile maps missing backend facts into invented product facts;
- recommendation logic and artifact loading have two plausible runtime homes;
- notebook outputs have filenames but no trustworthy experiment boundary.

The optimization target is therefore **Depth and Locality**, not more layers.
Each approved Module should hide one difficult policy behind one stable Seam so
callers cannot partially implement it.

## Candidate F — Runtime and delivery foundation

**Problem owned:** clean migration failure, unsupported Node baseline, known
dependency advisories, missing mobile lint/behaviour gates, stale setup docs.

**Deepening direction:** establish one reproducible delivery baseline in which a
clean database, backend checks, supported mobile runtime, and a small set of
journey checks are the executable definition of a valid workspace.

**Why this is high leverage:** every later architecture change depends on a
fresh database and trustworthy verification. It removes environment ambiguity
without changing product policy.

**Locality gain:** runtime versions, setup, migration proof and verification
commands become one coherent delivery contract instead of scattered README,
AGENTS, package and developer-machine assumptions.

**Required proof before exit:** clean Postgres upgrade to `0018`, backend full
validation, Node 24 TypeScript/Expo checks, dependency-audit disposition, and
repeatable smoke commands.

## Candidate A — Booking Integrity Module

**Problem owned:** over-capacity and past bookings, mock-slot fallback, unclear
slot identity, pricing/payment invention, and client-only validation.

**Deepening direction:** make reservation of a server-owned slot the single
Seam for creating a booking. Its Implementation owns date, capacity, business
hours, product availability, concurrency and transaction boundaries. Mobile
selects an offered slot; it does not reproduce scheduling policy.

**Why this is high leverage:** player booking, admin workload, analytics,
check-in, payments and future FYP2 features all consume this invariant.

**Locality gain:** all reasons a booking can or cannot exist are tested in one
domain location and committed in one transaction.

**Required proof before exit:** concurrent/full-slot rejection, past/closed-day
rejection, valid reservation success, API-contract tests, and browser journeys
without mock-to-live submission.

## Candidate C — Catalog and Inventory Aggregate

**Problem owned:** stock-driven visibility, hybrid metadata loss, non-atomic
admin saves, absolute rather than delta movements, and incomplete price data.

**Deepening direction:** define one domain-owned update boundary for catalog
identity/visibility, technical specification, commercial price and inventory.
These concepts can remain in one product Module while preserving their distinct
invariants. A client must not infer one field from another or issue a partial
sequence that can corrupt the aggregate.

**Why this is high leverage:** the same string record feeds discovery,
recommendation, booking, admin inventory and analytics.

**Locality gain:** hybrid-field preservation, visibility policy and inventory
movement semantics become server-owned and transactionally testable.

**Required proof before exit:** hidden positive-stock items stay hidden,
out-of-stock visibility follows an approved policy, hybrid fields round-trip,
failed updates are atomic, movement deltas audit correctly, and price
incompleteness is represented honestly.

## Candidate B — Mobile Data Boundary

**Problem owned:** 1,072-line broad store, mixed live/mock ownership, invented
payment/customer facts, manual server-state hydration, conditional hooks, and
non-persistent backend sessions.

**Deepening direction:** separate domain-local client state from remote server
state and put the live/mock choice behind an explicit development Seam. Each
screen consumes a truthful domain representation; missing backend data remains
missing rather than being fabricated from mocks or current catalog values.

**Why this is high leverage:** every Mobile route currently depends directly or
indirectly on the broad store; a narrower boundary reduces the blast radius of
all FYP2 screens.

**Locality gain:** authentication, catalog, booking and recommendation request
lifecycle each have one owner, while purely local UI state remains local.

**Required proof before exit:** no Rules-of-Hooks violations, mapper contract
tests, explicit offline/error states, agreed session lifecycle, truthful admin
customer/payment rendering, and core player/admin browser journeys.

## Candidate D — Recommendation Runtime Module

**Problem owned:** canonical scorer plus unused legacy adapter stack, eager
artifact loading, stale provenance updates, mismatched docs and unsupported
explanation copy.

**Deepening direction:** choose one runtime recommendation Module and make
artifact version/provenance part of its boundary. Compatibility Implementations
must either sit behind that Seam with a demonstrated caller or leave the startup
path. Explanation output should expose only evidence actually produced by the
selected scorer.

**Why this is high leverage:** recommendation results, audits, player trust,
catalog handoff and FYP2 model integration all depend on knowing which
Implementation and artifact produced a score.

**Locality gain:** scoring weights, feature mapping, provenance and explanation
semantics change together instead of across runtime, old AI service, Mobile copy
and documentation.

**Required proof before exit:** one identified runtime path, deterministic
fixture scores, artifact/provenance assertions, no obsolete startup file
dependency, correct percentage/tension rendering, and evidence-bound copy.

## Candidate E — NLP Experiment Boundary

**Problem owned:** review leakage, broken notebook syntax, unexecuted notebooks,
overwritten `latest` outputs, optional historical filenames and no run manifest.

**Deepening direction:** treat an experiment run as an immutable unit containing
input identity, review-level split, dictionary/config versions, code/notebook
version, metrics and versioned outputs. Promotion to backend consumption remains
a separate human-approved Seam.

**Why this is high leverage:** it converts notebook output from an informal file
drop into defensible FYP2 evidence without rewriting the notebook into a
production service.

**Locality gain:** data lineage, leakage checks, metrics and generated artifacts
are evaluated together; backend runtime remains independent of training tools.

**Required proof before exit:** syntax-clean top-to-bottom isolated execution,
zero review/text cross-partition leakage, immutable output paths, generated
manifest, reproducible metrics, and explicit promotion approval. The protected
ZIP and raw extracted data remain read-only.

## Recommended sequence for discussion

```text
F Runtime foundation
  -> A Booking integrity
  -> C Catalog/inventory aggregate
  -> B Mobile data boundary
  -> D Recommendation runtime
  -> E NLP experiment boundary
  -> full regression and final FYP2 approval
```

Rationale:

1. **F first** makes every later result reproducible and establishes Node 24 as
   a supported baseline.
2. **A before new features** closes the demonstrated data-integrity hole at the
   heart of the player/admin flow.
3. **C before broad Mobile reshaping** defines truthful server contracts for the
   most corruption-prone admin path.
4. **B then consumes stable contracts** and removes silent live/mock behaviour
   without guessing future backend shapes.
5. **D before E promotion** gives the offline experiment a single destination
   and provenance contract.
6. **E last in the architecture sequence** does not mean NLP is optional; it
   means training/evaluation work begins only after the promotion boundary is
   explicit. Its P0 leakage must still be resolved before FYP2 approval.

Candidates D and E may be designed together but should retain separate runtime
and experimentation ownership.

## Proposed approval gates

### Gate 1 — Review and candidate selection (current stop)

User approves, reorders or rejects architecture candidates. Until then:

- no architecture edits;
- no defect fixes;
- no dependency or Node pin changes;
- no notebook run;
- no FYP2 feature development.

### Gate 2 — Candidate design approval

For the first approved candidate, create a bounded design record containing its
domain invariants, current callers, data/schema impact, compatibility plan,
tests, rollback and task cards. Exact Interfaces are proposed here and reviewed
with the user before implementation.

### Gate 3 — Per-candidate implementation

Execute only the approved task card. At each boundary:

1. preserve unrelated and protected state;
2. implement the smallest coherent vertical slice;
3. run targeted tests and the candidate's acceptance proof;
4. update evidence and report remaining findings;
5. stop for approval before the next candidate.

### Gate 4 — Complete regression

After all approved blocker/high-risk work:

- migrate a new database to head;
- run Backend Ruff, format, Mypy and Pytest;
- run Mobile lint/type/behaviour tests under Node 24;
- run player and admin browser acceptance journeys;
- execute the NLP pipeline only in its approved isolated/versioned mode;
- validate artifact hashes, provenance and backend handoff;
- repeat dependency and secret audits;
- reconcile setup, architecture, migration and scoring documentation.

### Gate 5 — FYP2 readiness decision

Produce a final pass/fail matrix for every P0/P1 finding and every accepted
architecture invariant. FYP2 feature development starts only after the user
explicitly approves this final gate.

## Decision requested at Gate 1

The recommended approval is the full sequence `F -> A -> C -> B -> D -> E`,
starting only with Gate 2 design for **F** and **A**. The user may instead choose
one candidate, change the order, or narrow its scope. No selection is assumed.
