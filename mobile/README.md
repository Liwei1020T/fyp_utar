# StringSense: AI-Driven Mobile Platform

StringSense is an AI-driven React Native mobile platform for badminton racket
string recommendation and service management. It is the mobile client for the
integrated FYP workspace; the original FYP1 claim boundary remains documented
separately while the current runtime also includes the completed FYP2
operations modules.

## Tech Stack
- **Framework:** Expo (React Native)
- **Navigation:** Expo Router (File-based)
- **UI System:** HeroUI Native
- **Styling:** Uniwind (Tailwind-based)
- **State Management:** Zustand for the authenticated session, API snapshots, backend-derived views, and transient drafts
- **Forms:** React Hook Form + Zod

## Features
- **Player Flow:**
  - Welcome, Login, and Registration.
  - Personalized Player Profile setup.
  - AI String Recommendation based on playing style and priorities.
  - Badminton String Catalog with detailed performance scores.
  - Booking system for stringing services with status tracking.
  - Persisted payment/wallet, notifications, booking support, racket passport,
    check-in, and completed-service feedback flows.
- **Admin Flow:**
  - Secure Admin Login.
  - Operational Dashboard with key metrics.
  - Booking search, counter check-in, complete service lifecycle, notes, and photos.
  - String Inventory Management, including atomic editor saves and media.
  - Payment verification, support reply/resolve/close, and service queue.
  - Business hours, store settings, persisted analytics, and recommendation-run audit.
- **Future extension:**
  - Generative AI assistant backed by a real model endpoint.
  - Advanced Recommendation Engine with NLP/DL.

## Project Structure
- `app/`: Expo Router screens and layouts.
- `components/ui/`: Reusable primitives wrapping HeroUI Native.
- `components/shared/`: Common layout components like `AppScreen` and `AppSection`.
- `services/`: Typed API access, DTO mapping, SecureStore persistence on native, and current-tab session persistence on Web.
- `global.css`: Root Uniwind + HeroUI Native style entry.
- `tailwind.config.js`: Shared design tokens for colors and radii.

## Getting Started

1. **Use the supported Node version:**
   ```bash
   nvm use
   ```

   The project pins Node `24.18.0` in `.nvmrc` and allows the `24.x` LTS line in `package.json`.

2. **Install Dependencies:**
   ```bash
   npm install
   ```

3. **Run the App in a browser:**
   ```bash
   EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:3001/api npm run web
   ```

4. **Run on Expo Go using a physical phone:**
   Start the backend from `../backend` with `--host 0.0.0.0`, then find the Mac Wi-Fi IP:
   ```bash
   rtk ifconfig en0
   ```

   Use the `inet` value as `<MAC_WIFI_IP>`:
   ```bash
   EXPO_PUBLIC_API_BASE_URL=http://<MAC_WIFI_IP>:3001/api npm run start -- --lan
   ```

   Example:
   ```bash
   EXPO_PUBLIC_API_BASE_URL=http://192.168.0.80:3001/api npm run start -- --lan
   ```

   Open Expo Go on the phone and scan the QR code. The phone and Mac must be on the same Wi-Fi. Do not use `localhost` or `127.0.0.1` for Expo Go because those point to the phone itself.

5. **Run Native Simulator Targets:**
   ```bash
   npm run ios
   npm run android
   ```

6. **Navigate:**
   - The app starts at the unified `/auth/login` screen; the backend account role decides whether login continues to Player or Admin.
   - Player flow now uses phone number + password against the Python backend.
   - Every admin route uses the Python backend or backend-derived persisted records.
   - Player accounts are created through registration.
   - Admin accounts are available only when the backend operator explicitly configures `SEED_ADMIN_ENABLED=true` and the companion `SEED_ADMIN_*` values; credentials are never bundled into the app.

## Styling Runtime
- `global.css` must stay imported from `app/_layout.tsx`.
- `metro.config.js` must stay wrapped with `withUniwindConfig(..., { cssEntryFile: './global.css' })`.
- HeroUI Native relies on `GestureHandlerRootView` and the Babel `react-native-worklets/plugin` setup for stable native behavior.

## Architecture Decisions
- **Modularity:** Separate domain logic (strings, bookings) from UI components.
- **Surgical UI:** Used HeroUI Native as the primary design system to ensure a premium, modern aesthetic out of the box.
- **Live backend boundary:** Every authenticated route uses the unified Python API or backend-derived persisted records. The mobile runtime contains no seeded mock session.
- **Session lifecycle:** Native builds keep the backend bearer token in Expo SecureStore. Web builds keep it only in the current tab's session storage. Both revalidate it through `/auth/me` before restoring the authenticated UI.
- **Failure boundary:** Missing sessions and failed live reads/writes fail closed; the UI never substitutes local business records or reports a local-only success.
- **Type Safety:** Strict TypeScript interfaces for all data models.

## Validation

```bash
npx tsc --noEmit
npm run lint -- --max-warnings=0
npx expo export --platform web --output-dir /tmp/stringsense-web-export
```

The latest complete customer and administrator browser acceptance is recorded
in
[`../docs/customer-admin-acceptance-2026-07-24.md`](../docs/customer-admin-acceptance-2026-07-24.md).

---
Built for FYP 2026.
