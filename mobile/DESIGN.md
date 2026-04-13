# StringSense Mobile Design System

## Direction

StringSense should feel like a premium, practical badminton service app: calm enough for bookings, sharp enough for performance advice, and clear enough for a shop admin working quickly at the counter.

The UI uses a clean sports-service palette instead of a one-color blue system. Blue is reserved for primary player actions, teal supports service/status moments, amber marks highlights and attention, and neutral surfaces carry the layout.

## Color Roles

- Page: `#F7F9FC`
- Auth page: `#FAFBFD`
- Admin page: `#F6FAF8`
- Surface: `#FFFFFF`
- Muted surface: `#EEF3F7`
- Primary action: `#2563EB`
- Service accent: `#0F9F8F`
- Highlight accent: `#D48A12`
- Success: `#168A5B`
- Warning: `#B7791F`
- Danger: `#D94848`
- Text primary: `#14181F`
- Text secondary: `#566579`
- Border: `#DDE6F0`

## Layout Rules

- Use `AppScreen` for every route-level screen.
- Keep page padding at 16px for mobile density and consistent tab alignment.
- Use `AppSection` for title/subtitle rhythm instead of screen-local header blocks.
- Prefer two-column quick actions only when labels fit at 320px; otherwise stack.
- Horizontal carousels should align to page padding and keep a visible next-card hint.
- Bottom tabs float with 16px side gutters, compact height, and stable icon boxes.

## Component Rules

- Cards use `AppCard`; do not create new card chrome in screen files unless a domain component needs it.
- Buttons use `AppButton`; primary actions should be blue, service/admin secondary actions can use teal, and attention actions can use amber.
- Inputs use `AppInput`; field borders should stay visible on light backgrounds.
- Icon buttons use square 8px corners for a cleaner app-shell feel.
- Avoid heavy nested cards. One surface should be enough for most content blocks.
- Use Lucide icons consistently and keep icon sizes between 16 and 24 in content.

## Typography

- Use system sans-serif through `HeroText`.
- Letter spacing should remain normal for mobile readability.
- Section titles: 18-20px, semibold/bold.
- Card titles: 14-17px, semibold/bold.
- Metadata: 11-13px, medium, with strong contrast.
- Uppercase labels are allowed, but do not add wide tracking.

## Elevation

- Default cards: white surface, visible neutral border, light shadow.
- Elevated cards: same surface with slightly stronger border and shadow.
- Highlight cards: soft primary/amber/teal background, not saturated fills.
- Dark hero cards: use `appChromeColors.hero` sparingly for the main recommendation/action moment only.

## Accessibility

- All interactive `Pressable`/button-like components need `accessibilityRole="button"` when they are not a native button wrapper.
- Do not use color as the only status signal; combine chips, labels, and icons.
- Text contrast must remain readable on soft fills and dark hero cards.
- Avoid layout shift on press states; opacity or very small transform is acceptable.

## Current Optimization Notes

- The shared theme now balances blue, teal, amber, and neutral surfaces.
- Shared cards, buttons, inputs, headers, and tabs use tighter geometry and clearer borders.
- Player home quick actions and trending string cards use distinct action colors and denser spacing.
- Future screen-specific cleanup should replace hard-coded `#2F64B6` usages with `appChromeColors.primary` or the correct semantic color.
