# StringSense interface system

## Product direction

StringSense is a task-first badminton service product for players and a single shop operator. The interface should feel clear, trustworthy, calm, and lightly athletic. It is not a marketing dashboard.

### Modern mobile expression

- Use one strong task-focused scene per screen, supported by quieter modules.
- Favor confident color blocking, compact icon containers, and asymmetric content rhythm over repetitive card grids.
- Borrow the polish of contemporary mobile product concepts without hiding labels, inventing gestures, or showing fictional data.
- Keep player screens approachable and energetic; keep admin screens denser and operational.

## Hierarchy

- Put the next useful action before metrics or explanatory content.
- Use one page title, one primary action, and clear section titles.
- Prefer spacing and dividers over nested cards. Use cards only for grouped records, interactive destinations, or state that needs separation.
- Keep every feature reachable from Home or Profile for players and Overview for admins.

## Visual system

- System font stack; body text is at least 14pt and inputs are 16pt.
- Primary blue: `#2563EB`; dark brand surface: `#163B7A`.
- Page: `#F7F8FA`; surface: `#FFFFFF`; muted surface: `#F3F6FA`.
- Primary text: `#0F172A`; secondary text: `#475569`; border: `#D8E0EA`.
- Radius scale: 10 for controls, 14 for cards, 16 for prominent grouped regions.
- Shadow is reserved for floating navigation and overlays; ordinary cards use a border.

## Layout

- Phone gutters: 16; tablet: 24; desktop web: 32.
- Content max width: 960. Long text should remain narrower inside its feature component.
- Spacing follows a 4/8 rhythm with 16 between related elements and 24-32 between sections.
- Touch targets are at least 44pt and bottom navigation has at most five labeled destinations.

## Motion

- Animate at most the page header and main content group on route entry.
- Web uses GSAP; native uses Reanimated. Both use the same 220-240ms ease-out rhythm.
- Animate only opacity and transform. Never block input or animate layout dimensions.
- Respect system reduced-motion preferences and keep content immediately usable.

## Platform behavior

- Preserve Expo Router routes and native back behavior.
- Use native-safe controls and safe areas on iOS and Android.
- shadcn influences information hierarchy and component restraint, but web-only shadcn components are not imported into the Expo runtime.
