# AGENTS.md - mobile

This file applies to this directory and all children. Deeper `AGENTS.md` files override it.

## Mission

- Maintain the StringSense frontend as a production-shaped Expo Router prototype for badminton string recommendation and service management.
- Optimize for correctness, structure fidelity, and maintainability over quick one-off patches.
- Keep the player and admin flows realistic, coherent, and easy to extend into a real backend later.

## Project Context

- Primary users: badminton players booking stringing services, and one shop admin managing operations.
- Product shape: one codebase inside the unified StringSence workspace, two role-based experiences, premium mobile UI, with an API-only runtime data layer.
- Current runtime: authenticated pages use the Python backend or backend-derived records across every route; there is no local mock session or seeded runtime fallback.
- Non-goals: backend implementation, multi-store architecture, or inventing new tooling that does not exist in the repo.

## Canonical Commands

- Required Node line: `24.x` LTS
- Pinned project version in `.nvmrc`: `24.18.0`
- Setup: `nvm use` then `npm install`
- Run web: `npm run web`
- Run iOS: `npm run ios`
- Run Android: `npm run android`
- Lint: `npm run lint -- --max-warnings=0`
- Typecheck: `npx tsc --noEmit`
- Focused tests: `npm test`
  Prefer running this after `nvm use` so it uses the `.nvmrc`-pinned Node `24.18.0`.

## Validation Reality

- There is no `npm run build` script. Focused policy tests use Node's built-in test runner through `npm test`.
- For UI or flow changes, use the smallest truthful validation available:
  - `npm run lint -- --max-warnings=0`
  - `npx tsc --noEmit` under the `.nvmrc`-pinned Node `24.18.0`
  - `npm test` for pure session and contract policies
  - `npm run web` for runtime smoke validation
  - targeted manual route checks for touched flows
- If a check cannot be run, mark it `unverified` and explain why.

## Architecture Map

- App shell: `app/_layout.tsx`
  Owns global providers, `global.css`, HeroUI Native, native secure-session bootstrap, and the root Expo Router stack.
- Root redirect: `app/index.tsx`
  Sends unauthenticated users to `/auth/login` and authenticated users to `/player` or `/admin` based on session state.
- Access control: `app/auth/_layout.tsx`, `app/player/_layout.tsx`, `app/admin/_layout.tsx`, `components/roles/RoleGuard.tsx`
  Auth screens reject logged-in users; player and admin route groups are role-guarded.
- Player workspace: `app/player/(tabs)` plus detail flows under `app/player/**`
  Covers recommendation, catalog, booking, tracking, profile, booking support, payment, wallet, racket history, notifications, check-in, and feedback.
- Admin workspace: `app/admin/(tabs)` plus operations screens under `app/admin/**`
  Covers dashboard, read-only operations, booking, and inventory Admin AI queries, bookings, recommendation audit, inventory, business hours, check-in, support chat, analytics, payments, service queue, and settings.
- UI system: `components/ui/**`, `components/shared/**`
  `AppScreen`, `AppSection`, `AppButton`, `AppCard`, `AppChip`, `AppInput`, `AppIconButton`, and `theme.ts` define the shared look and layout behavior.
- Admin inventory components: `components/admin/inventory/**`
  Shared thumbnail cards and preview cards for the admin inventory workbench and detail editor live here.
- State and mutation boundary: `store/appStore.ts`
  In-memory source of truth for the authenticated session, API response snapshots, admin/store snapshots, compare selection, and booking drafts.
- API and mapping helpers: `services/backendClient.ts`, `services/backendApi.ts`, `services/backendMappers.ts`
  The client owns fetch, timeout, error, and 401 handling; the API facade owns endpoint calls; mappers translate live DTOs into the app domain. Missing sessions or failed API requests must fail closed.
- Session storage: `services/backendSessionStorage.ts`
  Native bearer tokens use Expo SecureStore. Web bearer tokens use current-tab session storage so refresh and deep links work without creating a long-lived browser login. Both are revalidated through `/auth/me`.
- Data contracts: `types/domain.ts`
  Canonical shared domain model. For inventory work, treat `StringItem.catalog` as master string data and `StringItem.inventory` as vendor-specific shop data; any top-level fields are mapper/UI projections only and are not database columns.
- Deep-dive reference: `docs/frontend-architecture.md`
  Update this doc when major structure or data-flow assumptions change.

## Critical Paths

- Auth redirect and role routing:
  `app/index.tsx` -> auth layout or role home -> role guard
- Player core journey:
  auth -> recommend/catalog -> string detail/compare -> booking draft -> booking summary confirmation -> booking detail/tracking
- Admin core journey:
  auth -> operations dashboard -> counter check-in/bookings/inventory/recommendation runs -> booking, inventory, or recommendation detail -> operational updates
- Shared state mutation hotspots:
  `updateBusinessHours`, `updateStringItem`, `updateStoreSettings`, and the live-data snapshot setters

## Structure Rules

1. Preserve the route-group structure.
   Put auth screens under `app/auth`, player screens under `app/player`, and admin screens under `app/admin`.
2. Reuse the shared screen shell first.
   New screens should normally be built with `AppScreen` and `AppSection` before introducing layout exceptions.
3. Keep app-level UI primitives in `components/ui`.
   If a pattern repeats across screens, promote it into a shared primitive instead of duplicating screen-local markup.
4. Keep domain types centralized in `types/domain.ts`.
   Do not redefine booking, payment, chat, racket, or admin/store-operation shapes inside screens.
   For inventory changes, preserve the separation between `catalog` master data and `inventory` shop data instead of flattening new admin logic into ad-hoc screen state.
5. Keep mutable business behavior in the store, not scattered across screens.
   Screens may derive display state, but durable mutations should live in `store/appStore.ts`.
6. Keep runtime data API-only.
   Pages must use backend DTOs, persisted booking history, or persisted commerce records. Never add seeded records or local success fallbacks to runtime routes.

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
- Browser web: start with `EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:3001/api npm run web`
- Expo Go on a physical phone:
  - Start the sibling backend in `../backend` with `./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload`
  - Run `ifconfig en0` from the workspace and copy the `inet` Wi-Fi IP
  - Start with `EXPO_PUBLIC_API_BASE_URL=http://<MAC_WIFI_IP>:3001/api npm run start -- --lan`
  - Keep the phone and Mac on the same Wi-Fi
  - Do not use `localhost` or `127.0.0.1` for Expo Go on a physical phone
- Start the sibling backend in `../backend` when testing live player flows
- Create a player through `/auth/register` or use an existing local backend player account for the player flow
- Never bundle or document fixed admin credentials in the app. Admin accounts must be configured explicitly with backend `SEED_ADMIN_*` environment values.

## Maintenance Rule

This file must stay executable and current. If you notice a placeholder, stale command, wrong path, outdated structure note, or missing architectural rule while working in this repo, update `AGENTS.md` as part of that task instead of leaving it drifted.
