# AGENTS.md - mobile

This file applies to this directory and all children. Deeper `AGENTS.md` files override it.

## Mission

- Maintain the StringSense frontend as a production-shaped Expo Router prototype for badminton string recommendation and service management.
- Optimize for correctness, structure fidelity, and maintainability over quick one-off patches.
- Keep the player and admin flows realistic, coherent, and easy to extend into a real backend later.

## Project Context

- Primary users: badminton players booking stringing services, and one shop admin managing operations.
- Product shape: one codebase inside the unified StringSence workspace, two role-based experiences, premium mobile UI, with a hybrid data layer.
- Current runtime split: FYP1 player/admin core flows may use the Python backend, while deferred FYP2 domains remain hidden, local, or mock-first.
- Non-goals: backend implementation, multi-store architecture, or inventing new tooling that does not exist in the repo.

## Canonical Commands

- Required Node line: `20.x`
- Pinned project version in `.nvmrc`: `20.19.0`
- Setup: `nvm use` then `npm install`
- Run web: `npm run web`
- Run iOS: `npm run ios`
- Run Android: `npm run android`
- Typecheck: `npx tsc --noEmit`
  Prefer running this after `nvm use` so it uses the `.nvmrc`-pinned Node `20.19.0`.

## Validation Reality

- There is no `npm run build`, `npm run lint`, or `npm test` script in this repo today. Do not invent them.
- For UI or flow changes, use the smallest truthful validation available:
  - `npx tsc --noEmit` under the `.nvmrc`-pinned Node `20.19.0` when possible
  - `npm run web` for runtime smoke validation
  - targeted manual route checks for touched flows
- If a check cannot be run, mark it `unverified` and explain why.

## Architecture Map

- App shell: `app/_layout.tsx`
  Owns global providers, `global.css`, HeroUI Native, React Query, and the root Expo Router stack.
- Root redirect: `app/index.tsx`
  Sends users to `/auth/welcome`, `/player`, or `/admin` based on session state.
- Access control: `app/auth/_layout.tsx`, `app/player/_layout.tsx`, `app/admin/_layout.tsx`, `components/roles/RoleGuard.tsx`
  Auth screens reject logged-in users; player and admin route groups are role-guarded.
- Player workspace: `app/player/(tabs)` plus detail flows under `app/player/**`
  Covers recommendation, catalog, booking, payment, tracking, chat, profile, wallet, rackets, and notifications.
- Admin workspace: `app/admin/(tabs)` plus operations screens under `app/admin/**`
  Covers dashboard, bookings, inventory, chat, analytics, business hours, check-in, payments, queue, and settings.
- UI system: `components/ui/**`, `components/shared/**`
  `AppScreen`, `AppSection`, `AppButton`, `AppCard`, `AppChip`, `AppInput`, `AppIconButton`, and `theme.ts` define the shared look and layout behavior.
- State and mutation boundary: `store/appStore.ts`
  Mutable runtime source of truth for session, bookings, payments, chat, notifications, wallet, rackets, admin settings, and drafts.
- Read helpers: `services/mockAppService.ts`, `services/backendApi.ts`, `services/backendMappers.ts`
  Mock lookups stay available, while the player core flow can map live backend data into the app domain.
- Data contracts: `types/domain.ts`
  Canonical shared domain model.
- Seed data: `mocks/**`
  Mock datasets for all feature domains.
- Deep-dive reference: `docs/frontend-architecture.md`
  Update this doc when major structure or data-flow assumptions change.

## Critical Paths

- Auth redirect and role routing:
  `app/index.tsx` -> auth layout or role home -> role guard
- Player core journey:
  auth -> recommend/catalog -> string detail/compare -> booking draft -> payment -> booking detail/tracking -> feedback
- Admin core journey:
  auth -> dashboard -> bookings/chat/inventory -> booking or inventory detail -> operational updates
- Shared state mutation hotspots:
  `submitBookingPayment`, `updateBookingStatus`, `appendChatMessage`, `requestAdminSupport`, `topUpWallet`, `updateBusinessHours`, `updateStringItem`

## Structure Rules

1. Preserve the route-group structure.
   Put auth screens under `app/auth`, player screens under `app/player`, and admin screens under `app/admin`.
2. Reuse the shared screen shell first.
   New screens should normally be built with `AppScreen` and `AppSection` before introducing layout exceptions.
3. Keep app-level UI primitives in `components/ui`.
   If a pattern repeats across screens, promote it into a shared primitive instead of duplicating screen-local markup.
4. Keep domain types centralized in `types/domain.ts`.
   Do not redefine booking, payment, chat, racket, or admin/store-operation shapes inside screens.
5. Keep mutable business behavior in the store, not scattered across screens.
   Screens may derive display state, but durable mutations should live in `store/appStore.ts`.
6. Treat the player core flow as hybrid.
   Player auth, profile, strings, recommendation, bookings, booking photos/comments, and FYP1 admin booking, inventory, business-hours, and limited store-settings operations may use the live backend, while FYP2 player/admin domains stay mocked or hidden.

## Runtime and Styling Constraints

1. `global.css` must stay imported from `app/_layout.tsx`.
2. `metro.config.js` must remain wrapped with `withUniwindConfig(..., { cssEntryFile: './global.css' })`.
3. `babel.config.js` must keep `react-native-worklets/plugin` unless the runtime setup is intentionally changed.
4. Preserve HeroUI Native + Uniwind patterns; do not swap to unrelated web-only component patterns.
5. Keep the player/admin visual split aligned with `components/ui/theme.ts`.

## Change Rules

1. Prefer minimal diffs that fit the existing architecture.
2. Reuse established patterns before adding new abstractions.
3. When adding a new feature area, place it in the existing route/domain structure instead of creating parallel organization.
4. When commands, architecture, or file structure change, update this `AGENTS.md` in the same task.
5. When a change materially affects architecture or developer orientation, also update `docs/frontend-architecture.md`.
6. Never commit secrets or private credentials.

## Definition of Done

1. The requested change follows the existing route, UI, and state structure.
2. Relevant checks were run and reported truthfully, or explicitly marked `unverified`.
3. No repo-specific runtime rules were broken.
4. `AGENTS.md` was updated if commands, structure, or architectural guidance changed.
5. `docs/frontend-architecture.md` was updated if the structural change is important enough that a future engineer would otherwise be misled.

## High-Risk Changes (Ask Before Proceeding)

- Destructive operations (`rm -rf`, hard reset, history rewrite, force push)
- Irreversible data/schema migrations
- Production auth/security/infra changes
- Large dependency or tooling upgrades
- Reorganizing route groups, store shape, or the shared UI system in ways that change multiple feature boundaries at once

## Quick Start

- Use `nvm use`
- Install with `npm install`
- Start with `EXPO_PUBLIC_API_BASE_URL=http://localhost:3001/api npm run web`
- Start the sibling backend in `../backend` when testing live player flows
- Use `+60123456789` / `password` for the player flow
- Use `+60190000000` / `admin1234` for the seeded backend admin flow when `SEED_ADMIN_ENABLED=true`

## Maintenance Rule

This file must stay executable and current. If you notice a placeholder, stale command, wrong path, outdated structure note, or missing architectural rule while working in this repo, update `AGENTS.md` as part of that task instead of leaving it drifted.
