# StringSense Frontend Architecture

## 1. Overview

StringSense is an Expo + React Native frontend for a badminton string recommendation and service management product. Every authenticated route uses the unified Python API or backend-derived persisted records. The mobile runtime has no seeded mock session or local business-data fallback.

The app is optimized for:

- fast FYP prototyping
- realistic FYP delivery flows with live backend persistence
- strong visual consistency through shared UI primitives
- role-based navigation for player and admin experiences

At runtime, player auth, profile, strings, recommendations, bookings, support messages, payments, wallet, notifications, racket service history, check-in, feedback, and the admin operations surface use live backend state.

The player home `Featured strings` carousel and store-hours summary are backend-backed through the existing store settings flow. Admins manage the featured string IDs and business hours from their existing settings screens, the backend persists them on the existing admin endpoints, and player surfaces hydrate both through `GET /api/store-settings` before rendering only the admin-picked strings and current opening status.

## 2. Technology Stack

### Core framework

- Expo
- React Native
- Expo Router for file-based navigation
- TypeScript

### UI and styling

- HeroUI Native for component primitives
- Uniwind + Tailwind-style utility classes
- Shared design tokens in `components/ui/theme.ts`
- Global style entry in `global.css`

### State and data

- Zustand for authenticated session state, live backend snapshots, and transient UI drafts
- Shared transport through `services/backendClient.ts`, typed endpoint calls through `services/backendApi.ts`, and DTO mapping through `services/backendMappers.ts`

### Forms and validation

- React Hook Form
- Zod

## 3. System Shape

```mermaid
flowchart TD
    A[Expo Router Entry] --> B[app/_layout.tsx]
    B --> C[Providers]
    C --> C1[GestureHandlerRootView]
    C --> C2[HeroUINativeProvider]
    B --> D[Root Stack]
    U[Native SecureStore] --> V[services/backendSessionStorage.ts]
    W[Web Current-Tab Session Storage] --> V
    V --> B

    D --> E[app/index.tsx]
    E --> F{Authenticated?}
    F -->|No| G[/auth]
    F -->|Player| H[/player]
    F -->|Admin| I[/admin]

    H --> J[RoleGuard player]
    I --> K[RoleGuard admin]

    J --> L[Player Tabs + Detail Screens]
    K --> M[Admin Tabs + Detail Screens]

    R[Unified Python API app/main.py] --> C4[services/backendClient.ts]
    C4 --> S[services/backendApi.ts]
    S --> T[services/backendMappers.ts]
    T --> O
    O --> L
    O --> M

    Q[components/ui + components/shared] --> L
    Q --> M
```

## 4. App Shell and Bootstrapping

The root application shell lives in `app/_layout.tsx`.

Responsibilities:

- imports `global.css`
- wraps the app in `GestureHandlerRootView`
- injects `HeroUINativeProvider`
- restores native tokens from SecureStore and web tokens from current-tab session storage
- revalidates every restored token through `/auth/me` before auth redirects resolve
- scopes 401 handling to the exact bearer token that failed, so a delayed
  request from an old session cannot clear a newer login
- renders an Expo Router `Stack` with hidden native headers

This file is the composition root for the frontend.

## 5. Routing and Access Control

### Root routing

- `app/index.tsx` redirects based on `useCurrentUser()`
- unauthenticated users go to the unified `/auth/login` screen
- authenticated users go to the role home returned by `getRoleHome()`

### Route groups

#### `app/auth`

Used for unauthenticated entry:

- `welcome`
- `login`
- `register`
- `forgot-password`

`app/auth/_layout.tsx` redirects authenticated users away from auth screens and into their role home.

#### `app/player`

Protected by `components/roles/RoleGuard.tsx` with `role="player"`.

Main tab workspace:

- `home`
- `strings`
- `More`, which opens the grouped player-tools sheet
- `bookings`
- `profile`

The `recommend`, `chat`, and `results` routes remain registered in the tab
group as flow targets, but they are not visible bottom-tab destinations. The
More sheet exposes recommendation, booking, support, notification, racket, and
wallet entry points without adding more bottom-tab items.

Additional stack screens extend the tab workflow:

- booking creation, summary, detail, and tracking
- string detail, compare, and explanation
- profile edit
- the all-tools screen and More-sheet entry point
- payment, feedback, racket service history, notifications, wallet, and counter check-in

`app/player/index.tsx` redirects to `/player/home`.

#### `app/admin`

Protected by `RoleGuard` with `role="admin"`.

Main tab workspace:

- `dashboard`
- `bookings`
- `inventory`
- `chat`
- `analytics`

Additional operational stack screens:

- booking detail
- inventory detail
- business hours
- settings
- check-in for order-ID-based counter drop-off confirmation
- recommendation run history and detail review for admin audit of saved recommendation outputs
- payments monitor, service queue, and human-support chat detail

`app/admin/index.tsx` redirects to `/admin/dashboard`.

### Guard model

`RoleGuard` enforces role access at the route-group level:

- no user -> redirect to `/auth/login`
- wrong role -> redirect to that user’s correct role home
- valid role -> render a stack with hidden headers

This keeps authorization logic centralized instead of repeating it in every screen.

## 6. State Architecture

The frontend’s mutable source of truth is `store/appStore.ts`.

### Store contents

The store owns:

- current session state, including refresh-time backend session bootstrap state
- live player/admin profiles, strings, bookings, and recommendation results
- live payment snapshots
- persisted support conversation snapshots
- live backend notifications and persisted read state
- business hours
- live physical racket passports and completed service history
- live wallets and transactions
- single-store settings
- compare selection
- booking draft

### Store actions

The store handles session, successful API snapshots, and transient UI state:

- backend session hydration, native SecureStore persistence, current-tab web session persistence, and refresh-time revalidation
- logout and successful player-profile replacement
- booking draft creation and clearing
- string compare selection
- successful business-hours, inventory, notification-read, and store-settings snapshots
- atomic upsert actions for bookings, payments, conversations, and rackets so
  concurrent successful requests cannot overwrite sibling updates with a
  captured screen snapshot

Payment, wallet, support-chat, and live booking writes call `backendApi.ts`
directly. The store receives the successful backend response as a replacement
snapshot; it does not simulate those writes locally.

### Derived accessors

The store file also exports convenience hooks such as:

- `useCurrentUser`
- `useBookings`
- `usePayments`
- `useConversations`
- `useNotifications`
- `useBusinessHoursState`
- `useStrings`
- `useRackets`
- `useWallets`

This keeps screens relatively simple while avoiding a separate selector layer.

### Runtime and Bundling Constraints

- To avoid `import.meta` ESM web errors during Expo Metro bundling, `babel.config.js` extends `babel-preset-expo` with `unstable_transformImportMeta: true` and `metro.config.js` prioritizes `.js` over `.mjs` in `sourceExts`.
- Zustand is kept at version 4.x to maintain broad Expo Metro compatibility without triggering advanced ESM edge cases.

## 7. Data Layer Model

The current frontend uses one runtime data path.

### 7.1 Mutable runtime state: `store/appStore.ts`

This is the display state after the app starts. Screens read Zustand snapshots,
while the backend remains authoritative for live-session writes.

Examples:

- newly created bookings
- updated profile data
- modified business hours
- wallet, payment, and conversation snapshots returned by the backend

### 7.2 Unified backend bridge

`services/backendClient.ts`, `services/backendApi.ts`, and
`services/backendMappers.ts` provide:

- phone-based player auth against the Python backend
- player password recovery code request/reset against the Python backend
- live player profile reads/writes
- live string catalog reads
- live booking reads/creates
- live confidence-aware recommendation requests
- persisted booking-linked and general-support conversations
- server-owned payment quotes, payments, wallet top-ups, and wallet history
- owned notifications, read IDs, preferences, rackets, and feedback
- administrator inventory, booking, check-in, queue, commerce, store, analytics,
  and recommendation-audit operations

The mapped backend responses are normalized back into the RN domain model so most screens can keep their existing structure.

The transport module owns the 12-second timeout, JSON/form/text response
handling, normalized backend errors, and token-specific 401 callback. The app
expires a session only when the failed token still matches the current token;
a late response from an older request cannot log out a newer session. Backend
tests compare the facade's route strings with generated OpenAPI paths, and the
pure session policy has a Node built-in test.

All writes reach a backend endpoint before the store is updated. A missing
token or failed request leaves the previous snapshot unchanged and presents an
error; no route creates local business records as a fallback.

## 8. Domain Model

Core shared interfaces are defined in `types/domain.ts`.

### Main entities

- `PlayerProfile`
- `AdminProfile`
- `StringItem`
- `Booking`
- `Payment`
- `ChatConversation`
- `ChatMessage`
- `NotificationItem`
- `RacketPassport`
- `BusinessHours`
- `BookingSlot`
- `AdminAnalyticsSummary`

### Inventory modeling note

`StringItem` is the shared mobile read model, but admin inventory treats two
nested records as the persistence source of truth:

- `catalog`
- `inventory`

`catalog` holds string master data such as names, hybrid identity, main/cross gauges, material, description, performance scores, image, and visibility state.

`inventory` holds vendor-specific data such as stock quantity, price, price status, availability status, and shop note.

Top-level string fields, where present, are mapper/UI projections for existing
player screens. They are not persisted backend columns or separate database
records.

The live admin detail editor commits changed catalog, official-performance, and inventory sections through one backend editor command and one database transaction. Image upload/removal remains a separate file-storage operation and is reported independently if it fails after the structured save.

### Important enums and unions

- `UserRole`
- `BookingStatus`
- `PaymentStatus`
- `PaymentMethod`
- `ConversationMode`
- `NotificationCategory`
- `InventoryAvailability`

This file is the canonical contract for app data and should stay in sync with any future backend schema or API DTO mapping.

## 9. UI System

The app uses a layered component approach.

### 9.1 HeroUI wrapper layer

`components/ui/heroui.tsx` adapts HeroUI Native primitives into local aliases:

- `HeroButton`
- `HeroChip`
- `HeroTextField`
- `HeroSlider`
- `HeroText`

This wrapper is the UI-system boundary between third-party primitives and app-specific components.

### 9.2 App primitives

App-specific primitives live in `components/ui/`:

- `AppButton`
- `AppCard`
- `AppChip`
- `AppInput`
- `AppIconButton`
- `theme.ts`

These components define the product’s look and feel:

- rounded glassy cards
- role-aware surfaces
- standardized button variants
- shared shadows and emphasis patterns
- reusable status color mapping

### 9.3 Shared layout shell

`components/shared/` contains layout building blocks:

- `AppScreen` for page shell, safe area handling, optional header chrome, and bottom inset logic
- `AppPageHeader` for the unified mobile header system used by `AppScreen`
- `AppSection` for section headings, eyebrows, and spacing

These two components are the main reason screens feel visually consistent despite covering many different workflows.

## 10. Navigation UX Structure

### Player information architecture

The player experience is organized around a consumer lifecycle:

1. onboarding and authentication
2. recommendation discovery
3. string comparison and detail
4. booking configuration
5. booking summary confirmation
6. service tracking

Live support and retention modules:

- chat
- notifications
- rackets
- wallet
- payment
- feedback

### Admin Information Architecture

The admin workspace is structured as an operations console:

1. operations-first dashboard with compact counter actions
2. booking queue
3. inventory management
4. support, payments, analytics, and recommendation audit
5. business hours, counter check-in, store settings, and player racket-model management

Operational tools live outside the tabs:

- check-in for direct `awaiting_dropoff -> in_progress` processing
- business hours
- settings

The admin surface also includes live service queue, payments monitor, human support, and analytics.

## 11. Feature Module Breakdown

### Authentication

Files in `app/auth/` provide:

- role-based backend login
- player self-registration
- role-based welcome and backend login entry

### Recommendation and catalog

Main files:

- `app/player/(tabs)/recommend.tsx`
- `app/player/(tabs)/results.tsx`
- `app/player/recommend/explain/[id].tsx`
- `app/player/(tabs)/strings.tsx`
- `app/player/strings/[id].tsx`
- `app/player/strings/compare.tsx`

These screens call the backend recommendation endpoints, map cached/generated
results into mobile domain models, and present backend-derived match data with
concise Agent explanations. The player-facing detail prioritises the Agent's
dynamic fit explanation, current racket/tension context, and evidence that was
actually used in the run. Structured personal-history, community, and
similar-player badges remain conditional; the saved top reason is only the
fallback when the Agent cannot answer. The page still prioritises fit, booking
setup, availability, and actionable trade-offs instead of exposing the former
score-breakdown and review-support blocks.

The active backend-aligned recommendation contract now assumes:

- canonical player setup inputs include `preferred_feel`, `preferred_gauge`, and structured `recent_goal`
- `pref_value_for_money` comes directly from the Value for money slider
- backend rationale exposes only values that contribute to the active score or explain a rule adjustment
- explanation payloads identify the contributing feature layer and retain only evidence needed for ranking, audit, or player-facing explanation
- recommendation explanation prompts are grounded in the exact saved run and
  must omit personal, community, or similar-player claims when their usage flags
  are false
- recommendation detail screens show the returned match score, catalog price,
  availability, and suggested tension; `value_for_money` remains part of the
  saved scoring payload but is not rendered as a separate player score card

### Booking

Main files:

- `app/player/bookings/new.tsx`
- `app/player/bookings/summary.tsx`
- `app/player/bookings/[id].tsx`
- `app/player/bookings/[id]/tracking.tsx`

The live FYP1 flow is draft-based:

1. booking draft is created in Zustand
2. summary page reads the draft
3. summary confirmation creates the backend booking
4. optional booking photo is uploaded afterward through the booking update endpoint
5. booking status, comments, and photos hydrate from the backend

Payment, player check-in, and post-service feedback use persisted backend
records. Feedback is a dedicated structured record that is allowed once per
owned completed booking.

### Booking Support Chat

Shared components:

- `components/chat/ChatBubble.tsx`
- `components/chat/ConversationCard.tsx`

Live screen flows:

- player chat tab + detail
- admin chat tab + detail

Booking-linked support keeps one thread per booking. Players without a booking
can use one reusable general-support thread; its messages live in dedicated
support tables. Both thread types share the player/admin list, read, reply,
resolve, and close surfaces.

### Profile And Player Retention Modules

The profile captures recommendation preferences, while retention modules use live backend history:

- profile and priorities
- budget tier, preferred feel, and recent goal now persist through the backend profile contract
- owned physical racket passports and completed linked service history
- server-catalogued standard racket identity selection with an explicit custom
  `Other model` fallback; only the backend-issued key enables exact-model CF
- wallet top-up and balance
- notifications and preferences

### Admin Operations

Admin-specific screens model the operational back office:

- dashboard metrics
- bookings management
- inventory workbench, attention triage, and master-detail editing
- admin-managed racket models used by the player registration selector
- business hours
- shop settings

Service queue, payments monitor, human support, and analytics are live admin operations.

Supporting inventory UI now lives in `components/admin/inventory/`, where shared thumbnail cards and preview cards keep the list and detail editor aligned.

## 12. Styling and Theming

`components/ui/theme.ts` defines shared UI constants:

- page background colors
- role-specific page surfaces
- tab bar colors
- layout metrics
- header metrics
- performance accent themes
- chip variants for booking and payment statuses

The current theme intentionally separates:

- auth tone
- player tone
- admin tone

That separation is reinforced by route-group layouts and screen-level hero cards.

## 13. Unified Header System

The app now uses exactly three header types across player and admin pages.

### Visual direction

- Apple-inspired light UI with restrained, product-first chrome
- Light gray surfaces using `#F5F5F7` and near-black text using `#1D1D1F`
- Blue reserved mainly for interactive elements and task affordances
- Compact rounded containers with flatter presentation and minimal shadow
- Clean mobile-first spacing, no oversized hero-like header chrome

### Header types

1. `primary`
- Use for top-level list, queue, and dashboard pages.
- Structure: title, short subtitle, optional right-side action.
- No back button by default.
- Visual role: lighter, flatter, dashboard-like container.

2. `secondary`
- Use for detail and functional edit pages.
- Structure: back button, title, optional right-side action, optional short subtitle.
- Visual role: compact, functional, and quiet.

3. `flow`
- Use for recommendation, booking, payment, comparison, and other task-oriented screens.
- Structure: back button, task title, short subtitle.
- Visual role: directional and decision-focused, with the only explicit blue progress accent.

### Back button rules

- Show the back button on `secondary` and `flow` headers unless there is truly no meaningful previous step.
- Hide the back button on `primary` headers by default, even if the router technically can go back.
- For tab-root pages, prefer no back button to keep the information architecture stable.

### Right-side action rules

- At most one right-side action in the header.
- Use it for high-value actions only: notifications, share, edit, preferences, or logout.
- Prefer blue icon affordances instead of decorative colored containers.
- Avoid right-side actions on `flow` headers unless the task genuinely needs it; the default is no action to preserve focus.

### Typography hierarchy

- `primary` title: strongest emphasis in the system, about 20px semibold with tight tracking.
- `primary` subtitle: 1 to 2 short lines, summary-level only.
- `secondary` title: compact functional title, about 17px semibold.
- `secondary` subtitle: optional and brief.
- `flow` title: task language first, written as an action or decision context.
- `flow` subtitle: short next-step guidance, never paragraph-like.

### Height and spacing guidance

- `primary` header min height: about 88px
- `secondary` header min height: about 72px
- `flow` header min height: about 76px
- Top spacing from safe area to header: 16px
- Header internal horizontal padding: 16 to 20px depending on type
- Gap between header and page content: 16px via the shared `AppScreen` content spacing
- Subtitles should remain short enough to scan without pushing the header into hero-card territory
- Keep borders subtle and shadows minimal; elevation should come mostly from tone contrast, not floating-card effects

### Page mapping

Player `primary` pages:

- `/player`
- `/player/strings`
- `/player/bookings`
- `/player/results`
- `/player/profile`

Player `secondary` pages:

- `/player/strings/[id]`
- `/player/bookings/[id]`
- `/player/bookings/[id]/tracking`
- `/player/recommend/explain/[id]`

Player `flow` pages:

- `/player/recommend`
- `/player/strings/compare`
- `/player/bookings/new`
- `/player/bookings/summary`
- `/player/profile/edit`

Additional live player pages:

- `/player/tools`
- `/player/chat`
- `/player/chat/[id]`
- `/player/notifications`
- `/player/notifications/preferences`
- `/player/wallet`
- `/player/wallet/top-up`
- `/player/rackets`
- `/player/rackets/[id]`
- `/player/payments/[bookingId]`
- `/player/payments/[bookingId]/result`
- `/player/check-in`
- `/player/feedback/[bookingId]`

Admin `primary` pages:

- `/admin`
- `/admin/bookings`
- `/admin/inventory`

Admin `secondary` pages:

- `/admin/bookings/[id]`
- `/admin/inventory/[id]`
- `/admin/business-hours`
- `/admin/settings`
- `/admin/racket-models`

Admin `flow` pages:

- `/admin/check-in`
  Use for counter-side order lookup, drop-off checklist completion, and booking handover confirmation.

Additional live admin pages:

- `/admin/assistant`
- `/admin/chat`
- `/admin/chat/[id]`
- `/admin/analytics`
- `/admin/payments`
- `/admin/service-queue`
- `/admin/users`
- `/admin/recommendations`
- `/admin/recommendations/[runId]`

## 14. Screen Composition Pattern

Most screens follow the same structure:

1. `AppScreen`
2. unified `AppPageHeader` chrome selected through `AppScreen`
3. one or more `AppSection` blocks
4. feature-specific cards, chips, and buttons
5. CTA group near the bottom

This pattern makes the app easy to extend because new screens can remain visually consistent without introducing new layout systems.

## 15. Current Architectural Strengths

- Clear role separation between player and admin experiences
- Good domain typing in `types/domain.ts`
- Reusable layout and UI primitives reduce visual drift
- API-only runtime data ownership is explicit
- Route guards keep access control centralized
- Store actions capture meaningful product flows instead of only low-level field updates

## 16. Current Architectural Constraints

- Live request lifecycle and cache invalidation are still manually coordinated by layouts and screens
- Some business logic lives directly inside screens, especially ranking and feature-specific derivations
- Mobile unit coverage remains thin; route behavior is currently protected by
  backend integration tests plus the browser acceptance record in
  `docs/customer-admin-acceptance-2026-07-24.md`

## 17. Recommended Evolution Path

The next evolution path is:

1. Keep `types/domain.ts` as the domain contract and map backend DTO changes explicitly
2. Choose one server-state owner for each domain before adding a cache library
3. Continue narrowing Zustand toward session state, snapshots, drafts, and transient local workflows
4. Keep `components/ui` and `components/shared` as the stable design-system layer
5. Preserve Expo Router route groups and role guards; they already map well to product boundaries

## 18. Directory Guide

### `app/`

Route-level UI and navigation entrypoints.

### `components/ui/`

Low-level app primitives and theme tokens.

### `components/shared/`

Reusable layout shells used across many screens.

### `components/*`

Feature-specific reusable UI such as booking cards, the player More sheet, chat
bubbles, tracking timelines, payment cards, and analytics stats.

### `store/`

Application state, mutations, and convenience selectors.

### `services/`

Backend API access, DTO mapping, and session persistence.

### `types/`

Shared domain contracts.

### `lib/`

Formatting and lightweight navigation helpers.

### `tests/`

Small compatibility smoke coverage.

## 19. Summary

The current frontend is a role-based Expo Router application with:

- a shared provider shell
- route-group access control
- centralized Zustand session and live-snapshot state
- persisted support conversations, notification read state, and physical racket passports
- a persisted payment and wallet workflow
- a reusable HeroUI-based design system
- feature modules covering the full player and admin journeys

It is best understood as a production-shaped FYP workspace: every authenticated route page has an API or backend-derived persisted data path and fails closed when that path is unavailable.
