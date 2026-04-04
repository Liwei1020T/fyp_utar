# StringSense: AI-Driven Mobile Platform

StringSense is an AI-driven React Native mobile platform for badminton racket string recommendation and service management. This prototype is built for FYP 1, demonstrating a premium sports-tech UI and clean architecture.

## Tech Stack
- **Framework:** Expo (React Native)
- **Navigation:** Expo Router (File-based)
- **UI System:** HeroUI Native
- **Styling:** Uniwind (Tailwind-based)
- **State Management:** Zustand (Hybrid Local State), React Query provider for future and partial live data use
- **Forms:** React Hook Form + Zod

## Features
- **Player Flow:**
  - Welcome, Login, and Registration.
  - Personalized Player Profile setup.
  - AI String Recommendation based on playing style and priorities.
  - Badminton String Catalog with detailed performance scores.
  - Booking system for stringing services with status tracking.
- **Admin/Vendor Flow:**
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

   The project now pins Node `25.9.0` in `.nvmrc` and allows the `25.x` line in `package.json`.

2. **Install Dependencies:**
   ```bash
   npm install
   ```

3. **Run the App:**
   ```bash
   npm run web
   ```

4. **Run Mobile Targets:**
   ```bash
   npm run ios
   npm run android
   ```

5. **Navigate:**
   - The app starts at `/auth/welcome`.
   - Player flow now uses phone number + password against the Python backend.
   - Vendor flow remains mock-based with `vendor@example.com` / `password`.

6. **Optional live backend override:**
   ```bash
   EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:3001/api npm run web
   ```

## Styling Runtime
- `global.css` must stay imported from `app/_layout.tsx`.
- `metro.config.js` must stay wrapped with `withUniwindConfig(..., { cssEntryFile: './global.css' })`.
- HeroUI Native relies on `GestureHandlerRootView` and the Babel `react-native-worklets/plugin` setup for stable native behavior.

## Architecture Decisions
- **Modularity:** Separate domain logic (strings, bookings) from UI components.
- **Surgical UI:** Used HeroUI Native as the primary design system to ensure a premium, modern aesthetic out of the box.
- **Hybrid Player MVP:** Player auth, profile, strings, recommendations, and bookings can use the live Python backend while vendor and advanced domains remain mock-backed.
- **Type Safety:** Strict TypeScript interfaces for all data models.

---
Built for FYP 2026.
