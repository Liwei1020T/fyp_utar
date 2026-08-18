# QR Payment and Proof Acceptance — 2026-08-18

## Implemented

- Admin Store Settings can upload, preview, replace, and delete the active
  payment QR.
- Player wallet top-up and booking payment expose `qr_transfer` and `cash`.
- New QR-transfer requests require a JPG, PNG, or WEBP screenshot up to 5 MB.
- Cash requests need no QR or screenshot and remain pending until the admin
  confirms receipt.
- Admin payment records show a short-lived proof URL/preview before approval.
- QR top-up approval credits the append-only wallet ledger exactly once.
- Cash top-up approval uses the same exactly-once wallet-credit path.
- Booking-payment approval does not advance booking workflow state.
- `wallet_balance` booking payment remains immediate and does not require a
  screenshot.
- Historical Card/Online banking/E-wallet rows remain readable and were not
  relabeled as evidence-backed QR transfers.

## Backend Evidence

- Alembic head: `20260818_0032`.
- Disposable SQLite migration upgrade reached the new head successfully.
- `tests/test_commerce_quote.py`: 3 passed, including QR upload/replace/delete,
  media download, QR payment proof, no-QR rejection, and pending cash
  booking/top-up approval behavior.
- `tests/test_notifications.py`: 10 passed.
- Full backend suite: 151 passed, 2 skipped.
- Ruff check and format check passed.
- Mypy passed for 214 source files.

## Mobile Evidence

- TypeScript: passed.
- Expo lint with zero warnings: passed.
- Mobile policy tests: 10 passed.
- Expo Web export: passed with 3,677 modules.

## Security Boundaries Verified

- Uploads use existing magic-byte, MIME, size, UUID filename, and traversal
  validation.
- New files are removed on transaction rollback; replaced QR files are removed
  only after commit.
- Payment proof URLs are short-lived (15 minutes) and are only returned by the
  existing owner-scoped or admin-scoped payment responses.
- Backend rejects paid approval for a new QR-transfer record without proof.
- Admin-only QR mutations remain behind the existing role guard.

## Unverified

- Real browser interaction was not completed because the local Playwright
  Chromium executable is not installed. Static export succeeded, but this is
  not claimed as browser acceptance.
- Physical Expo Go image-picker and QR save/open behavior still require a real
  device smoke.
- No external bank/e-wallet provider or webhook was added; admin review remains
  the deliberate FYP boundary.
