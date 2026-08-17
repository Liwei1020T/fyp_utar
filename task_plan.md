# Agent Scope Simplification Plan

## Goal

Keep only the FYP-focused Agent scope while preserving completed code for later re-enablement.

## Active Scope

- Player guided string selection.
- Exact recommendation explanation.
- Verified in-stock alternatives.
- Admin read-only operations summary.

## Deferred Scope

- Player comparison, review Q&A, store information, booking queries, saved/latest recommendation queries, and Agent-created handoff.
- Admin booking, inventory, payment, and support searches.
- Admin booking, inventory, and support write proposals.
- Source chips and suggested-question chips in the Agent answer card.

Deferred implementations remain in the repository and are disabled at their registration or UI exposure points with re-enable comments.

## Phases

### Phase 1 — Agent registration audit

**Status:** complete

### Phase 2 — Backend Agent simplification

**Status:** complete

### Phase 3 — Mobile Agent simplification

**Status:** complete

### Phase 4 — Agent documentation

**Status:** complete

### Phase 5 — Agent validation

**Status:** complete

### Phase 6 — Complete FYP2 delivery audit

**Status:** complete

### Phase 7 — Fresh validation and acceptance

**Status:** complete

### Phase 8 — Final completion classification

**Status:** complete

### Phase 9 — Current page inventory and isolated acceptance fixture

**Status:** complete

### Phase 10 — Authentication and player page-by-page acceptance

**Status:** complete

### Phase 11 — Admin page-by-page acceptance

**Status:** complete

### Phase 12 — Cross-role mutations, failure states, and persistence

**Status:** complete

### Phase 13 — Fresh quality gates and final page matrix

**Status:** complete

### Phase 14 — General human-support conversation scope

**Status:** complete

### Phase 15 — Repair confirmed page-review defects and copy issues

**Status:** complete

### Phase 16 — Verify official string data and schema/runtime provenance

**Status:** complete

### Phase 17 — Full regression, browser acceptance, and handoff

**Status:** complete

## Decisions

- Keep the admin read-only summary; disable all admin detailed queries and writes.
- Leave day-7/day-10 notification automation unchanged because it is not an Agent capability.
- Preserve authentication, ownership checks, output validation, rate limiting, and evidence grounding.
- Treat manual admin payment verification as the completed FYP payment design; a real gateway is an optional external integration unless the assessment explicitly requires it.
- Treat in-app notification delivery as complete and real WhatsApp receipt as incomplete until OpenWA is configured and verified on a phone.
- Treat fresh-database price setup, physical-phone smoke, and the booking-only human-support boundary as demo-readiness items that must be resolved or explicitly accepted.
- Use one isolated PostgreSQL database for the full page review; never mutate the retained demo database.
- Review only real renderable pages. Layout files, AppleDouble metadata, and redirect-only index routes are inventoried separately and are not counted as data pages.
- Report defects without changing product behavior unless the user separately asks for fixes.
- Keep booking-linked support and booking-free support as separate persisted
  records; reuse one general thread per player and route both through the same
  player/admin chat UI.
- Treat catalog source URLs and official-performance evidence as separate
  provenance layers; do not promote seeded feel values to official ratings.

## Errors Encountered

| Error | Attempt | Resolution |
|---|---:|---|
| `react/no-unescaped-entities` on the Admin AI heading | 1 | Escaped the JSX apostrophe and reran mobile validation. |
| Browser acceptance backend could not connect to PostgreSQL on port 55432 | 1 | Start the repository `postgres` service, verify health, then retry the backend. |
| Docker Desktop opened but its engine/socket remained unavailable | 2 | Use an isolated temporary SQLite database for UI acceptance without touching project data. |
| Admin Dashboard still described confirmed Agent actions | 1 | Updated the entry copy to describe the active read-only summary. |
| Playwright wrapper hit a root-owned user npm cache temp entry | 1 | Use an isolated npm cache under `/private/tmp` for remaining browser commands. |
| Fresh Playwright daemon could not write the macOS `ms-playwright` cache | 2 | Stop retrying global cache access; verify the final copy in the successful static export plus lint and TypeScript. |
| Docker Desktop quit request did not return | 1 | Stopped the waiting AppleScript; all task-owned backend and web-server processes were stopped. |
| Authenticated audit catalog read initially returned 401 | 1 | Reused the temporary player's bearer token without printing it; authenticated read returned 12 items. |
| Shell-local token assignment expanded before the curl header | 1 | Used direct command substitution from the task-owned temporary login response; token remained out of tool output. |
| Planning completion checker reported `8/0` because the older inline phase format lacked supported headings | 1 | Converted the plan to the skill's supported phase-heading and status format. |
| Expo Web dev server could not write the user-level `.expo/native-modules-cache` | 1 | Use the already validated production export and a task-owned stdlib SPA-rewrite server for direct route acceptance. |
| Initial fixture recommendation cache was invalidated by later feedback creation | 1 | Regenerated the player's recommendation after all feedback writes; this is expected cache invalidation, not a page defect. |
