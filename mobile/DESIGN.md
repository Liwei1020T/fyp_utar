# Design System Inspiration of Apple

## Visual Direction

StringSense should follow an Apple-inspired mobile UI: quiet surfaces, precise typography, clear hierarchy, restrained depth, and one unmistakable interactive accent. The interface should feel calm and product-focused rather than decorative.

The design rhythm is built from near-white backgrounds, white cards, occasional near-black feature panels, and Apple Blue for interactive elements. Color should not compete with the content. Badminton strings, bookings, and service status are the product; the UI should frame them cleanly.

## Color Palette

- Page background: `#F5F5F7`
- Surface: `#FFFFFF`
- Near black text: `#1D1D1F`
- Secondary text: `rgba(29, 29, 31, 0.72)`
- Tertiary text: `rgba(29, 29, 31, 0.48)`
- Border / separator: `#D2D2D7`
- Dark panel: `#1D1D1F`
- Dark panel elevated: `#272729`
- Primary interactive accent: `#0071E3`
- Link blue: `#0066CC`
- Blue on dark: `#2997FF`

Semantic status colors may remain for operational clarity, but they should stay soft and secondary. They must not become the main brand palette.

## Typography

- Use the system sans-serif through `HeroText`, matching the SF Pro feel where available.
- Keep letter spacing normal in the React Native app; avoid decorative wide tracking.
- Large screen titles: 20-30px, weight 600-700, tight but readable line height.
- Section titles: 18-20px, weight 700.
- Card titles: 14-17px, weight 600-700.
- Body and metadata: 12-15px, weight 400-600.
- Keep body text left aligned. Center alignment is only for small decorative product previews.

## Layout

- Use `AppScreen` for route-level screens.
- Use `AppSection` for section title/subtitle spacing.
- Keep mobile page padding compact and consistent at 16px.
- Prefer full-width content blocks over nested card stacks.
- Horizontal carousels should align to page padding and reveal a hint of the next card.
- Bottom tabs should float lightly above the page with a white translucent surface and a subtle border.

## Components

- Brand identity uses `AppBrandLogo` everywhere an in-app logo is shown; native and web app icons use the same `assets/icon.png` source.
- Cards use `AppCard`.
- Buttons use `AppButton`.
- Inputs use `AppInput`.
- Dropdowns use `AppSelect`: closed state shows one selected value, expanded state reveals the option list in place, and the selected option uses a check mark.
- Use `AppSelect` for single-choice fields and filters; reserve chips for multi-select tags, status badges, and quick actions.
- Icon buttons use `AppIconButton`.
- Use Lucide icons consistently.
- Use 10px radius for controls, 14px for cards and list rows, and 16px for page headers or feature panels.
- Pills are allowed only for chips and small labels.
- Avoid multiple nested borders inside cards unless the inner boundary has a clear functional purpose.

## Buttons

- Primary CTA: Apple Blue `#0071E3`, white text.
- Secondary CTA: white surface, visible neutral border, near-black or link-blue text.
- Dark CTA: near-black fill, white text.
- Button corners: 10px for standard actions and 14px for large full-width actions.
- Press feedback should be subtle opacity or a tiny scale change.

## Cards And Elevation

- Default cards: white background, neutral border, light shadow.
- Elevated cards: white background, very soft diffused shadow.
- Highlight cards: soft blue tint, not saturated color blocks.
- Dark hero cards: near-black background with white text, reserved for the main advisory/feature moment.
- Avoid heavy colored glow except for focused interactive moments.

## Page Rhythm

- Light informational screens should use `#F5F5F7` page background.
- White cards should feel like product tiles on a neutral canvas.
- Dark panels should be rare, high-impact moments.
- The app should not read as a blue dashboard; blue is for action and focus.

## Accessibility

- All custom pressable controls need `accessibilityRole="button"` when appropriate.
- Text contrast must meet mobile readability expectations.
- Do not communicate status with color alone; use chips, labels, or icons.
- Keep tap targets at least 40px high where possible.

## Implementation Notes

- `components/ui/theme.ts` owns shared color constants.
- `global.css` mirrors the same visual tokens for HeroUI Native and Uniwind.
- `tailwind.config.js` should keep primary, secondary, and accent aligned to Apple Blue rather than unrelated accent hues.
- Screen-local hard-coded colors should be replaced with shared tokens when touched.
