# StringSense: AI-Driven Mobile Platform

StringSense is an AI-driven React Native mobile platform for badminton racket string recommendation and service management. This prototype is built for FYP 1, demonstrating a premium sports-tech UI and clean architecture.

## Tech Stack
- **Framework:** Expo (React Native)
- **Navigation:** Expo Router (File-based)
- **UI System:** HeroUI Native
- **Styling:** Uniwind (Tailwind-based)
- **State Management:** Zustand for session, live snapshots, mock-only deferred domains, drafts, and local mutations
- **Forms:** React Hook Form + Zod

## Features
- **Player Flow:**
  - Welcome, Login, and Registration.
  - Personalized Player Profile setup.
  - AI String Recommendation based on playing style and priorities.
  - Badminton String Catalog with detailed performance scores.
  - Booking system for stringing services with status tracking.
- **Admin Flow:**
  - Secure Admin Login.
  - Operational Dashboard with key metrics.
  - Booking Management and Status Updates.
  - String Inventory Management.
- **Coming in FYP 2:**
  - Real-time AI Chatbot Assistant.
  - Advanced Recommendation Engine with NLP/DL.

## Project Structure
- `app/`: Expo Router screens and layouts.
- `components/ui/`: Reusable primitives wrapping HeroUI Native.
- `components/shared/`: Common layout components like `AppScreen` and `AppSection`.
- `mocks/`: Realistic badminton data layer.
- `services/`: API abstraction layer for both mocks and the live player backend bridge.
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
   - The app starts at `/auth/welcome`.
   - Player flow now uses phone number + password against the Python backend.
   - Admin FYP1 booking, inventory, business-hours, and limited store-settings flows can use the Python backend.
   - Player accounts are created through registration.
   - Admin accounts are available only when the backend operator explicitly configures `SEED_ADMIN_ENABLED=true` and the companion `SEED_ADMIN_*` values; credentials are never bundled into the app.

## Styling Runtime
- `global.css` must stay imported from `app/_layout.tsx`.
- `metro.config.js` must stay wrapped with `withUniwindConfig(..., { cssEntryFile: './global.css' })`.
- HeroUI Native relies on `GestureHandlerRootView` and the Babel `react-native-worklets/plugin` setup for stable native behavior.

## Architecture Decisions
- **Modularity:** Separate domain logic (strings, bookings) from UI components.
- **Surgical UI:** Used HeroUI Native as the primary design system to ensure a premium, modern aesthetic out of the box.
- **Hybrid FYP1 MVP:** Player auth, profile, strings, recommendations, bookings, booking updates, and FYP1 admin operations can use the live Python backend while deferred FYP2 domains remain hidden, local, or mock-backed.
- **Session lifecycle:** Native builds keep the backend bearer token in Expo SecureStore and revalidate it at startup. Web sessions remain memory-only and require login after a full refresh.
- **Live/mock boundary:** Backend sessions fail closed when live users, strings, or bookings are missing; mock records are never used as a fallback for a live API submission.
- **Type Safety:** Strict TypeScript interfaces for all data models.

---
Built for FYP 2026.
