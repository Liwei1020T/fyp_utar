# Production Hardening and Acceptance Record (2026-08-24)

## Result

StringSence is ready for an FYP demonstration and for a controlled,
single-host deployment after real secrets, a public API hostname, and a
Cloudflare Tunnel token are supplied. The large-file split requested for
exclusion was not performed.

This is not a claim of fully managed high-availability production. WhatsApp,
the public Cloudflare route, external Agent delivery, backup restoration, and
real payment QR data remain explicit operator acceptance gates.

## Hardening delivered

- Production Docker image runs as UID/GID 10001, contains only runtime files,
  has a health check, and uses a frozen dependency lock.
- Production Compose isolates PostgreSQL on an internal network, publishes no
  backend or database host port, runs Alembic as a one-shot service, mounts only
  uploads as writable storage, drops Linux capabilities, and uses bounded logs.
- Optional `cloudflared` is pinned and reaches the backend through the private
  Compose edge network. It is profile-gated and cannot start without the token.
- Production startup rejects weak JWT secrets, wildcard trusted hosts, insecure
  CORS origins, reset-code preview, and weak placeholder seed-admin passwords.
- Production API docs are disabled and responses include host validation,
  HSTS, anti-sniffing, frame, referrer, and permissions headers.
- Inactive or missing inventory is now unavailable at the shared catalog policy
  boundary, with a regression test.
- Admin booking lists and player booking details refresh from the backend when
  focused, fixing cross-account stale state found during browser acceptance.
- Expo 54 patch dependencies were aligned. Safe transitive overrides remove the
  fixable `brace-expansion` and `js-yaml` advisories without a major migration.

## Real acceptance evidence

Runtime: the production image plus a fresh isolated PostgreSQL 16.15 volume,
with a loopback-only acceptance override for the browser.

| Check | Evidence | Result |
| --- | --- | --- |
| Empty database migration | Alembic upgraded a new database to `20260818_0032 (head)` | Pass |
| Production startup | Backend and PostgreSQL became healthy; 108 recommendation matrix rows imported | Pass |
| Container boundary | Production base Compose exposes no host ports; backend runs as `stringsense` with a read-only root filesystem | Pass |
| Security response | `/health` returned 200 with HSTS, frame denial, no-sniff, referrer, and permissions headers | Pass |
| PostgreSQL concurrency | Capacity and security race tests ran against a separate PostgreSQL database | 2 passed |
| Player onboarding | Registered `acceptance-player`, completed preferences, and generated live recommendations | Pass |
| Booking capacity | Fresh defaults correctly had no slots; admin opened Tuesday 09:00-17:00 and 16 slots appeared | Pass |
| Booking creation | Player booked JS-63 at 25 lbs for 2026-08-25 09:00; booking `ORD-F4FDE` persisted | Pass |
| Cross-role refresh | Admin list loaded the new booking after the focus-refresh fix | Pass |
| Service workflow | Admin moved the same booking through In Progress, Ready for Collection, and Completed | Pass |
| Player status refresh | Player loaded the persisted Completed state and full timeline | Pass |
| Feedback loop | Player submitted 5/5 service feedback; admin feedback page showed the same order and comment | Pass |
| Browser stability | Player and admin journeys completed with zero console errors | Pass |

Local screenshot evidence is under ignored `output/playwright/`:
`player-home.png`, `booking-confirmed.png`, and `feedback-submitted.png`.

## Automated verification

- Backend: Ruff check and format check passed; mypy passed for 199 source files;
  pytest `158 passed, 2 skipped`; all 37 installed Python packages compatible.
- Mobile: Node tests `10 passed`; TypeScript, Expo lint, and Expo Web production
  export passed (3,677 modules).
- NLP workbench: `43 passed`.
- Docker: curated backend image built successfully; Compose config parsed;
  migration, health check, matrix import, and fresh PostgreSQL runtime passed.

The two backend skips are expected optional-integration cases, not failures.

## Remaining gates

1. Create the Cloudflare Tunnel and public hostname, put its token in the
   untracked production env file, then run the public HTTPS smoke test.
2. Configure WhatsApp/OpenWA and perform QR/session/API-key plus real-phone
   receipt acceptance. It remains disabled now as requested.
3. Supply a real Agent provider key before claiming live DeepSeek delivery.
4. Configure real store identity, address, prices, payment notes, and payment QR
   before customer deployment; no business values were invented for acceptance.
5. Perform encrypted off-host backup and restore rehearsal for PostgreSQL and
   the uploads volume before storing real customer/payment data.
6. `npm audit --omit=dev` reports one unfixed `image-size` denial-of-service
   advisory through the Expo/Metro toolchain (49 transitive paths). There is no
   compatible fix in the current Expo 54 line. Do not process untrusted assets
   in the build pipeline; reassess during a separately tested Expo major upgrade.

Keep one backend worker for this deployment. Add a database-unique job claim or
an external scheduler before scaling horizontally.

## Operator handoff

Follow [`deploy/README.md`](../deploy/README.md). The tunnel service URL is
`http://backend:3001`; PostgreSQL and FastAPI should remain unpublished.
