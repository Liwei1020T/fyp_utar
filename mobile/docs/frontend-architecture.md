# StringSense Frontend Architecture

## 1. Overview

StringSense is an Expo + React Native frontend prototype for a badminton string recommendation and service management product. The current frontend is now a hybrid system: the player MVP flow can use the live Python backend, while the admin workspace and non-core domains remain mock-first inside one codebase.

The app is optimized for:

- fast FYP prototyping
- realistic product flows without a real backend
- strong visual consistency through shared UI primitives
- role-based navigation for player and admin experiences

At runtime, the app behaves like a full product. Player auth, profile, strings, recommendation, and booking flows can be hydrated from the backend, while the rest of the product still uses local mock modules and Zustand-managed prototype state.

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

- Zustand for application state, hybrid session state, and mock mutations
- React Query provider is installed at the app root and the player MVP flow can use live backend requests
- Local mock datasets in `mocks/` remain the source of truth for admin and advanced player features

### Forms and validation

- React Hook Form
- Zod

## 3. System Shape

```mermaid
flowchart TD
    A[Expo Router Entry] --> B[app/_layout.tsx]
    B --> C[Providers]
    C --> C1[GestureHandlerRootView]
    C --> C2[QueryClientProvider]
    C --> C3[HeroUINativeProvider]
    B --> D[Root Stack]

    D --> E[app/index.tsx]
    E --> F{Authenticated?}
    F -->|No| G[/auth]
    F -->|Player| H[/player]
    F -->|Admin| I[/admin]

    H --> J[RoleGuard player]
    I --> K[RoleGuard admin]

    J --> L[Player Tabs + Detail Screens]
    K --> M[Admin Tabs + Detail Screens]

    N[mocks/*] --> O[store/appStore.ts]
    N --> P[services/mockAppService.ts]
    R[stringsense_backend API] --> S[services/backendApi.ts]
    S --> T[services/backendMappers.ts]
    T --> O
    O --> L
    O --> M
    P --> L
    P --> M

    Q[components/ui + components/shared] --> L
    Q --> M
```

## 4. App Shell and Bootstrapping

The root application shell lives in `app/_layout.tsx`.

Responsibilities:

- imports `global.css`
- wraps the app in `GestureHandlerRootView`
- creates the global `QueryClient`
- injects `HeroUINativeProvider`
- renders an Expo Router `Stack` with hidden native headers

This file is the composition root for the frontend.

## 5. Routing and Access Control

### Root routing

- `app/index.tsx` redirects based on `useCurrentUser()`
- unauthenticated users go to `/auth/welcome`
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
- `recommend`
- `bookings`
- `chat`
- `profile`

Additional stack screens extend the tab workflow:

- booking creation, summary, detail, tracking, payment, and feedback
- string detail, compare, and explanation
- profile edit
- racket passport list/detail
- notifications and preferences
- wallet and top-up
- QR check-in

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
- payments monitor
- settings
- service queue
- check-in
- chat detail

`app/admin/index.tsx` redirects to `/admin/dashboard`.

### Guard model

`RoleGuard` enforces role access at the route-group level:

- no user -> redirect to `/auth/welcome`
- wrong role -> redirect to that user’s correct role home
- valid role -> render a stack with hidden headers

This keeps authorization logic centralized instead of repeating it in every screen.

## 6. State Architecture

The frontend’s mutable source of truth is `store/appStore.ts`.

### Store contents

The store owns:

- current session state (persisted via Zustand middleware to `localStorage` for web)
- backend player session bridge
- live player profile, strings, bookings, and recommendation results
- users
- strings
- bookings
- payments
- conversations
- notifications
- business hours
- rackets
- wallets and wallet transactions
- admin settings
- notification preferences
- compare selection
- booking draft
- last payment outcome

### Store actions

The store handles all user-visible prototype mutations:

- auth login, quick login, logout, player registration
- backend player session hydration and persistence
- player profile updates
- booking draft creation and clearing
- full booking payment flow
- booking cancellation
- admin booking status updates
- string compare selection
- chat message append, admin handoff request, and resolution
- business hours updates
- inventory updates
- notification read state
- wallet top-up
- notification preference updates
- admin settings updates

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

The current frontend uses two parallel data access patterns.

### 7.1 Mutable runtime state: `store/appStore.ts`

This is the live application state after the app starts. Once a user logs in or performs actions, screens should treat the Zustand store as the authoritative mutable state.

Examples:

- newly created bookings
- updated profile data
- modified business hours
- wallet balance changes
- new chat messages

### 7.2 Hybrid player backend bridge

`services/backendApi.ts` and `services/backendMappers.ts` provide:

- phone-based player auth against the Python backend
- player password recovery code request/reset against the Python backend
- live player profile reads/writes
- live string catalog reads
- live booking reads/creates
- live rules-based recommendation requests

The mapped backend responses are normalized back into the RN domain model so most screens can keep their existing structure.

### 7.3 Read helpers over seed data: `services/mockAppService.ts`

This file exposes synchronous helper functions such as:

- `getStringById`
- `getBookingsForPlayer`
- `getAdminAnalytics`
- `getConversationsForAdmin`

These helpers read from `MOCK_*` constants and are mostly used for lookup convenience and screen composition.

### 7.4 Mock data sources: `mocks/`

The mock layer is split by domain:

- `users.ts`
- `strings.ts`
- `bookings.ts`
- `payments.ts`
- `slots.ts`
- `rackets.ts`
- `notifications.ts`
- `chats.ts`
- `analytics.ts`
- `businessHours.ts`
- `settings.ts`
- `wallet.ts`

`mocks/index.ts` re-exports these modules as a single import surface.

### Architectural note

The system currently mixes:

- direct reads from Zustand state
- direct reads from `services/mockAppService.ts`
- direct imports from mock constants in some screens

That is acceptable for the prototype, but in a production migration the service layer should become the single read boundary and the store should evolve into UI/session state on top of API-backed queries and mutations.

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
- `AppSection` for section headings, eyebrows, and spacing

These two components are the main reason screens feel visually consistent despite covering many different workflows.

## 10. Navigation UX Structure

### Player information architecture

The player experience is organized around a consumer lifecycle:

1. onboarding and authentication
2. recommendation discovery
3. string comparison and detail
4. booking configuration
5. payment
6. service tracking
7. post-service feedback

Support modules branch off that main flow:

- chat
- notifications
- profile
- rackets
- wallet

### Admin Information Architecture

The admin workspace is structured as an operations console:

1. dashboard snapshot
2. booking queue
3. inventory management
4. chat queue
5. analytics

Operational tools live outside the tabs:

- check-in
- service queue
- business hours
- payments monitor
- settings

## 11. Feature Module Breakdown

### Authentication

Files in `app/auth/` provide:

- role-based mock login
- player self-registration
- welcome screen for demo branching

### Recommendation and catalog

Main files:

- `app/player/(tabs)/recommend.tsx`
- `app/player/recommend/results.tsx`
- `app/player/recommend/explain/[id].tsx`
- `app/player/(tabs)/strings.tsx`
- `app/player/strings/[id].tsx`
- `app/player/strings/compare.tsx`

These screens compute ranking directly from player priority weights and string rating fields.

### Booking and payment

Main files:

- `app/player/bookings/new.tsx`
- `app/player/bookings/summary.tsx`
- `app/player/payments/[bookingId].tsx`
- `app/player/payments/[bookingId]/result.tsx`
- `app/player/bookings/[id].tsx`
- `app/player/bookings/[id]/tracking.tsx`
- `app/player/check-in.tsx`
- `app/player/feedback/[bookingId].tsx`

The flow is draft-based:

1. booking draft is created in Zustand
2. summary page reads the draft
3. payment action creates or updates a booking
4. status and notifications are updated in-store

### Chat

Shared components:

- `components/chat/ChatBubble.tsx`
- `components/chat/ConversationCard.tsx`

Screen flows:

- player chat tab + detail
- admin chat tab + detail

The same conversation model supports:

- AI-only mode
- waiting for admin
- admin joined
- resolved
- closed

### Profile, rackets, wallet, notifications

These modules capture the personalization and retention layer of the player product:

- profile and priorities
- racket passport history
- wallet top-up and balance
- notifications and preferences

### Admin Operations

Admin-specific screens model the operational back office:

- dashboard metrics
- bookings management
- inventory detail and stock controls
- service queue
- business hours
- payments monitor
- shop settings

## 12. Styling and Theming

`components/ui/theme.ts` defines shared UI constants:

- page background colors
- role-specific page surfaces
- tab bar colors
- layout metrics
- performance accent themes
- chip variants for booking and payment statuses

The current theme intentionally separates:

- auth tone
- player tone
- admin tone

That separation is reinforced by route-group layouts and screen-level hero cards.

## 13. Screen Composition Pattern

Most screens follow the same structure:

1. `AppScreen`
2. top hero or summary card
3. one or more `AppSection` blocks
4. feature-specific cards, chips, and buttons
5. CTA group near the bottom

This pattern makes the app easy to extend because new screens can remain visually consistent without introducing new layout systems.

## 14. Current Architectural Strengths

- Clear role separation between player and admin experiences
- Good domain typing in `types/domain.ts`
- Reusable layout and UI primitives reduce visual drift
- Mock-first architecture allows rapid demo iteration
- Route guards keep access control centralized
- Store actions capture meaningful product flows instead of only low-level field updates

## 15. Current Architectural Constraints

- Data access is split across store state, mock services, and direct mock imports
- React Query is initialized but not yet the primary data-fetching mechanism
- There is no dedicated repository/API client abstraction yet
- Some business logic lives directly inside screens, especially ranking and feature-specific derivations
- The test surface is currently very thin; the repo only includes a small HeroUI compatibility smoke component in `tests/heroui-compat.smoke.tsx`

## 16. Recommended Evolution Path

When this frontend moves beyond FYP mock mode, the cleanest migration path is:

1. Replace direct `MOCK_*` reads with API-backed query functions
2. Keep `types/domain.ts` as the domain contract and add mapping if backend DTOs differ
3. Move server data ownership to React Query
4. Narrow Zustand to session state, drafts, transient UI state, and optimistic local workflows
5. Keep `components/ui` and `components/shared` as the stable design-system layer
6. Preserve Expo Router route groups and role guards; they already map well to product boundaries

## 17. Directory Guide

### `app/`

Route-level UI and navigation entrypoints.

### `components/ui/`

Low-level app primitives and theme tokens.

### `components/shared/`

Reusable layout shells used across many screens.

### `components/*`

Feature-specific reusable UI such as booking cards, chat bubbles, tracking timelines, payment cards, and analytics stats.

### `store/`

Application state, mutations, and convenience selectors.

### `services/`

Read-oriented helper functions over the mock domain.

### `mocks/`

Seed datasets for all major product domains.

### `types/`

Shared domain contracts.

### `lib/`

Formatting and lightweight navigation helpers.

### `tests/`

Small compatibility smoke coverage.

## 18. Summary

The current frontend is a role-based Expo Router application with:

- a shared provider shell
- route-group access control
- a centralized Zustand mock-state store
- a mock service helper layer
- a reusable HeroUI-based design system
- feature modules covering the full player and admin demo journeys

It is best understood as a production-shaped prototype with a hybrid transition layer: the player MVP is now close to a real backend-connected product flow, while admin and advanced product areas remain intentionally local and mock-driven.
