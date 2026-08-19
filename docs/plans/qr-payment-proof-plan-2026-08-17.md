# QR Transfer and Payment-Proof Implementation Plan

> 2026-08-18 extension: new booking payments and wallet top-ups also accept
> `cash`. Cash reuses the same pending/admin-review ledger, requires no QR or
> proof image, and does not credit a wallet before admin approval.

## Status

- Planning: complete
- Implementation: complete, with browser/device checks explicitly unverified
- Scope: wallet top-up and booking payment only

## Outcome

Replace the three placeholder external payment choices with one truthful manual
`qr_transfer` flow:

1. The admin uploads and maintains the shop's payment QR in Store Settings.
2. A player previews or downloads the current QR, pays outside StringSence, and
   selects a payment screenshot.
3. The screenshot and payment request are submitted atomically as one pending
   payment.
4. The admin previews the evidence and marks the request paid, failed, or
   cancelled.
5. A paid wallet top-up credits the append-only wallet ledger exactly once; a
   paid booking payment changes only its payment record.

`wallet_balance` remains an immediate server-validated booking-payment option
and does not require a QR or screenshot.

## Explicit Non-Goals

- No FPX, bank, e-wallet, Stripe, webhook, OCR, or automatic receipt validation.
- No storage of card numbers, bank credentials, or transaction credentials.
- No fabricated default QR image; external transfer stays unavailable until an
  admin uploads a real QR.
- No separate top-up evidence table or second payment ledger.
- No user editing or deleting evidence after submission. A failed or cancelled
  request may be retried as a new payment.

## Existing Foundation to Reuse

- `payments` already owns booking payments and wallet top-ups.
- `wallet_transactions` is append-only and already enforces one ledger entry per
  completed payment.
- Admin payment decisions already lock a pending payment before updating it.
- `expo-image-picker`, multipart requests, image magic-byte validation, 5 MB
  limits, randomized upload names, signed media URLs, and transaction-aware file
  cleanup already exist.
- Store Settings already has authenticated admin read/write and authenticated
  player read paths.

## Proposed Data Contract

### Schema migration

Create proposed Alembic revision
`20260818_0032_qr_payment_proofs.py`, based on current head
`20260817_0031`:

- Add nullable `store_settings.payment_qr_path` (`Text`).
- Add nullable `payments.proof_path` (`Text`).
- Add a database check so `qr_transfer` payments require `proof_path`, while
  `wallet_balance` payments may keep it null.

Historical `card`, `online_banking`, and `e_wallet` rows remain unchanged because
they predate screenshot evidence. They stay readable and reviewable as legacy
records but are not accepted by new player-create requests. This avoids falsely
relabeling old records as evidence-backed QR transfers.

Only server-owned relative upload paths are persisted. API responses expose
derived media URLs, never filesystem paths.

### Public DTOs

- `StoreSettingsOut.payment_qr_url: string | null`
- `PaymentOut.proof_url: string | null`
- New-payment input methods become `qr_transfer | wallet_balance`; output types
  retain the three legacy method values for historical records.
- Wallet top-up creation always records `qr_transfer`; clients do not choose a
  fake provider label.

### Upload storage

Extend the current upload storage allowlist with:

- `payment-qr/` for the one active shop QR.
- `payment-proofs/` for immutable per-payment screenshots.

Reuse existing JPG/PNG/WEBP magic-byte checks, declared MIME matching, 5 MB
limit, UUID filenames, traversal protection, and transaction callbacks.

- A failed database transaction deletes the newly written file.
- Replacing the shop QR deletes the previous file only after the new path commits.
- Payment evidence is not deleted when an admin rejects a request; it remains
  audit evidence with the payment record.

QR media keeps the existing signed-media behavior. Proof URLs should be
short-lived signed URLs returned only from existing owner-scoped or admin-scoped
payment responses. The original upload filename and image bytes must not be
logged.

## API Plan

### Admin QR configuration

- `POST /api/admin/store-settings/payment-qr`
  - Admin authentication required.
  - Multipart field: `photo`.
  - Validates and atomically replaces the active QR.
  - Returns updated `StoreSettingsOut`.
- `DELETE /api/admin/store-settings/payment-qr`
  - Admin authentication required.
  - Clears the configured QR and removes the old file after commit.
  - Returns updated `StoreSettingsOut`.
- Existing `GET /api/store-settings` exposes the derived QR URL to authenticated
  players.

The existing JSON `PUT /api/admin/store-settings` remains responsible for text,
pricing, notifications, and featured strings. QR files do not get mixed into
that JSON request.

### Player payment submission

Keep the existing route names and change their create requests to multipart:

- `POST /api/payments/bookings/{booking_id}`
  - Fields: `method`, optional `expected_amount`, optional `proof`.
  - `qr_transfer` requires the current shop QR and a valid proof image.
  - `wallet_balance` rejects a proof and keeps the existing immediate ledger
    balance check.
- `POST /api/wallet/top-ups`
  - Fields: `amount`, required `proof`.
  - Server sets `method=qr_transfer`.
  - Requires the current shop QR before accepting the request.

For external transfers, save the proof and pending payment in one transaction.
Do not create a pending payment when file validation or persistence fails.
Existing duplicate-active-payment protection remains authoritative for booking
payments.

### Admin review

- Existing `GET /api/admin/payments` includes `proof_url`.
- Existing `PATCH /api/admin/payments/{payment_id}` remains the only decision
  endpoint.
- The backend rejects `paid` for any `qr_transfer` record without evidence,
  even if inconsistent legacy data somehow reaches the endpoint.
- Pre-existing pending legacy-method records remain reviewable under their old
  contract; no evidence is invented or backfilled for them.
- Existing row locking and terminal-state rule remain unchanged.

## Mobile Plan

### Shared QR transfer panel

Add one small shared payment component used by booking payment and wallet top-up:

- Current QR image and clear unavailable state.
- Full-screen QR preview.
- `Download QR` action: direct browser download on Web and system URL
  open/save flow on iOS/Android, using the existing media endpoint rather than a
  new mobile dependency.
- Screenshot selection through the installed `expo-image-picker`.
- Selected-image preview, replace, and remove-before-submit actions.
- Submit remains disabled until both a configured QR and screenshot exist.

### Admin Settings

Add a `Payment QR` section to `mobile/app/admin/settings.tsx`:

- Preview the current QR.
- Upload the first QR.
- Replace it independently from the normal `Save store settings` button.
- Delete it through the project's working Web/native confirmation pattern.
- Refresh the shared Store Settings state after each successful mutation.
- Explain that deleting the QR disables new external payments/top-ups but does
  not affect pending reviews.

### Player screens

- `mobile/app/player/wallet/top-up.tsx`
  - Remove Card/Online banking/E-wallet chips.
  - Show one QR-transfer path, amount controls, QR panel, screenshot picker, and
    `Submit for review`.
- `mobile/app/player/payments/[bookingId].tsx`
  - Offer only `QR transfer` and `Wallet balance`.
  - Show the QR panel only for QR transfer.
  - Preserve server quote, stale-quote conflict handling, insufficient-wallet
    checks, and duplicate-pending protection.
- Payment result and wallet pages continue showing pending/paid/failed state;
  copy changes from generic external payment to QR-transfer review.
- `mobile/app/admin/payments.tsx`
  - Show evidence thumbnail and full-screen preview for QR transfers.
  - Disable `Verify paid` if evidence is missing; keep reject/cancel available.
  - Preserve the existing irreversible-action confirmation and top-up consequence
    copy.

## Expected File Scope

Backend:

- `backend/migrations/versions/20260818_0032_qr_payment_proofs.py`
- `backend/app/adapters/persistence/sqlalchemy/models/commerce.py`
- `backend/app/adapters/persistence/sqlalchemy/models/store_settings.py`
- `backend/app/domain/store/entities.py`
- `backend/app/adapters/persistence/sqlalchemy/repositories/mappers.py`
- `backend/app/dto/commerce.py`
- `backend/app/dto/store.py`
- `backend/app/shared/upload_storage.py`
- `backend/app/entrypoints/api/routes/commerce_routes.py`
- `backend/app/entrypoints/api/routes/admin_routes.py`
- focused commerce/store tests

Mobile:

- `mobile/app/admin/settings.tsx`
- `mobile/app/admin/payments.tsx`
- `mobile/app/player/wallet/top-up.tsx`
- `mobile/app/player/payments/[bookingId].tsx`
- `mobile/app/player/payments/[bookingId]/result.tsx`
- `mobile/components/payment/QrTransferPanel.tsx`
- `mobile/services/backendApi.ts`
- `mobile/types/backend.ts`
- `mobile/types/domain.ts`
- `mobile/services/backendMappers.ts`
- one focused policy/contract test

Documentation:

- `backend/docs/api-contract.md`
- `backend/docs/database.md`
- `backend/docs/runbook.md`
- `docs/codebase-map.md`
- a dated QR-payment acceptance record after implementation

The implementation should avoid unrelated screen or architecture changes and
must preserve existing dirty/generated worktree files.

## Delivery Phases

### Phase 1 — Approved migration and storage primitives

- Recheck migration head and dirty worktree.
- Add the two path columns, legacy-preserving method constraint, and database
  invariant.
- Add QR/proof storage helpers and transaction-safe cleanup.
- Add focused invalid-file, rollback-cleanup, replace, and traversal tests.

### Phase 2 — Backend contracts and payment invariants

- Extend Store Settings mapping/DTOs and admin QR endpoints.
- Convert payment creation to multipart and require evidence for QR transfer.
- Preserve wallet balance behavior and exactly-once top-up credit.
- Expose derived QR/proof media URLs only through authorized records.
- Update focused backend tests before wider validation.

### Phase 3 — Admin QR management

- Add upload/preview/replace/delete controls to Admin Settings.
- Verify failed replacement leaves the old QR usable.
- Verify delete produces a truthful no-QR state for players.

### Phase 4 — Player QR and proof submission

- Add the shared QR panel.
- Update top-up and booking-payment choices and multipart clients.
- Preserve all current quote, ownership, active-payment, and wallet checks.

### Phase 5 — Admin evidence review

- Add evidence preview to payment cards.
- Preserve irreversible confirmation and terminal decisions.
- Verify booking payment and top-up consequences remain different.

### Phase 6 — Documentation and regression

- Update API, database, runbook, code map, and user-facing copy.
- Run targeted tests, then full backend/mobile checks.
- Run migration upgrade on a disposable PostgreSQL database.
- Perform browser acceptance for both roles and an Expo Go device smoke for
  image selection, preview, and QR save/open behavior when a device is available.
- Record any unperformed physical-device step as `unverified`, not passed.

## Required Test Matrix

Backend checks:

- Admin-only QR upload, replace, delete, and public authenticated read.
- JPG/PNG/WEBP accepted; empty, mismatched MIME/magic bytes, unsupported type,
  oversized file, and path traversal rejected.
- New QR replacement rollback preserves the old file/path.
- Booking QR payment requires configured QR, owned booking, current quote, and
  evidence.
- Wallet top-up requires configured QR, valid amount, and evidence.
- Wallet balance booking payment succeeds without evidence and rejects
  insufficient funds.
- Another player cannot list or obtain the proof URL for someone else's payment.
- Admin paid/failed/cancelled transitions remain pending-only.
- Repeating `paid` does not create a second wallet credit.
- Booking-payment approval does not advance booking status.
- Failed/cancelled requests allow a fresh later request with new evidence.
- Migration preserves legacy methods while enforcing the evidence invariant on
  every new `qr_transfer` row.

Mobile/browser checks:

- Admin can upload, preview, replace, and delete QR from Settings.
- Player sees the latest QR on both top-up and booking payment screens.
- Preview and download/open actions work without exposing a local server path.
- Submit is disabled without QR or proof and shows file-validation errors.
- Admin can preview the exact submitted evidence before deciding.
- Approved top-up appears once in wallet balance/ledger after player refresh.
- Approved booking payment appears paid without changing booking workflow state.
- Existing wallet-balance checkout remains functional.

## Validation Commands

Targeted first:

```bash
cd backend && ./.venv/bin/pytest -q tests/test_commerce_quote.py tests/test_unified_backend_flows.py
cd mobile && PATH=/Users/lwt/.nvm/versions/node/v24.18.0/bin:$PATH npm test
```

Full gates:

```bash
cd backend && ./.venv/bin/ruff check . && ./.venv/bin/ruff format --check . && ./.venv/bin/mypy app ai_service tests && ./.venv/bin/pytest -v
cd mobile && PATH=/Users/lwt/.nvm/versions/node/v24.18.0/bin:$PATH npm run lint -- --max-warnings=0
cd mobile && PATH=/Users/lwt/.nvm/versions/node/v24.18.0/bin:$PATH npx tsc --noEmit
git diff --check
```

Migration/runtime acceptance must use a disposable database unless the user
separately authorizes changing the retained demo database.

## Definition of Done

- A real admin-provided QR can be uploaded, previewed, replaced, and deleted.
- Both player flows preview/download that QR and submit a validated screenshot.
- Every QR transfer becomes a persisted pending payment with immutable evidence.
- Admin can inspect evidence before a terminal decision.
- Top-up approval credits exactly once; booking-payment approval does not mutate
  booking workflow state; wallet-balance checkout remains unchanged.
- Ownership, file validation, signed-media expiry, rollback cleanup, and database
  invariants have runnable coverage.
- Relevant docs match the implemented contract.
- Targeted and full checks pass, with device-only checks explicitly classified.

## Approval Gate

Implementation approval was received on 2026-08-18. The implementation is
complete only after the delivery phases and validation gates below pass.
