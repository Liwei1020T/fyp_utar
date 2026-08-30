# FYP-Scoped Player And Admin Agent

## Active Scope

The FYP keeps one focused player recommendation Agent and one optional read-only
admin operations surface:

- `/player/chatbot`: asks exactly one question at a time for playing style,
  preferred feel, durability importance, and maximum RM budget, then returns up
  to three recommendation-preview results. It compares two or three approved
  strings, introduces an exact catalog string when the detail page supplies its
  verified context, answers live customer-facing store information, and provides
  a direct user-owned entry to the existing human support screen.
- `/player/results`: renders one short Agent-generated fit summary for each
  shortlisted string when its exact recommendation run is available.
- `/player/recommend/explain/[id]`: explains the exact owned recommendation run
  in short player-friendly language and offers verified in-stock alternatives
  when the selected string is unavailable.
- `/admin/assistant`: returns the current read-only operations summary and can
  search booking and inventory records. It does not propose changes.

DeepSeek composes the response but never ranks strings. The existing V11
recommendation use case remains the only ranking owner, and guided previews do
not update the saved profile or recommendation cache.

## Active Backend Boundary

Player model-call tools:

- `get_string_details`
- `compare_strings`
- `get_store_information`
- `preview_recommendation_what_if`
- `find_in_stock_alternatives`

The exact recommendation page also preloads the authenticated player's owned
`run_id` and matching string data directly through the backend. The preload
reader remains available internally without being exposed as a general model
tool.

Admin model-call tools:

- `get_admin_operations_summary`
- `find_admin_bookings`
- `find_admin_inventory`

The only active response action is `open_string`, used to open a verified
replacement string. Evidence status and source metadata remain in the API
response for audit, but evidence-status, source, and suggested-question chips
are hidden in the reduced mobile UI.

## Deferred But Preserved

The completed implementations remain in the repository and are not deleted.
They are excluded from the active allowlists or hidden at the UI exposure point:

- Player review Q&A, owned-booking lookup, saved-preference lookup,
  latest-recommendation lookup, and Agent-created human handoff.
- Admin payment and support searches.
- Admin booking-status, stock-count, and support-reply proposals and their
  confirmation handlers.
- Evidence-status chips, source chips, suggested-question chips, and the broader
  starter prompts.

Notification follow-ups are not Agent behavior. The existing day-7/day-10 App
and configured WhatsApp workflow remains separate and unchanged by this scope
reduction.

The visible `Contact human support` button is active and opens a persisted
general-support conversation even when the player has no booking. Booking-linked
support remains available for order-specific questions. Only model-triggered or
automatic handoff remains deferred.

## Re-Enabling Deferred Capabilities

1. Uncomment the required name in `ACTIVE_AGENT_TOOL_NAMES` or
   `ACTIVE_ADMIN_AGENT_TOOL_NAMES`.
2. If an action is required, uncomment it in `ACTIVE_AGENT_ACTIONS`.
3. Restore the broader prompt by assigning
   `DEFERRED_BROAD_CHATBOT_INSTRUCTION` or
   `DEFERRED_ADMIN_ASSISTANT_INSTRUCTION` to the active instruction constant.
4. Uncomment the matching mobile starter/action entry. Set `showEvidenceStatus`,
   `showSources`, or `showSuggestedQuestions` to `true` if those presentation
   extras are needed.
5. Update the active-scope regression test and run the backend and mobile
   validation commands before claiming the capability is restored.

Do not enable only the mobile button or only the model tool. Tool registration,
action validation, prompt scope, UI exposure, tests, and this document must move
together.

## Configuration

Keep the API key only in the untracked `backend/.env`:

```env
AGENT_ENABLED=true
AGENT_API_KEY=your-deepseek-api-key
AGENT_MODEL=deepseek-v4-flash
AGENT_BASE_URL=https://api.deepseek.com
AGENT_TIMEOUT_SECONDS=20
AGENT_MAX_TOOL_ROUNDS=2
```

The Agent is disabled by default. Missing configuration returns `503`, while
the recommendation detail page can still display its saved deterministic
rationale.

## Safety Rules That Remain Active

- Authentication, role checks, and player ownership checks.
- Twelve queries per authenticated user per minute for the current
  single-process FYP deployment.
- Validated tool calls, arguments, JSON responses, and verified resource IDs.
- At most two tool rounds and three calls per round by default.
- Server-built source metadata and one-way hashed provider user identifiers.
- Plain, concise user-facing copy without internal calculation details.
- No direct model writes to application state.

The support conversation tables are part of the unified backend migration chain;
they are application support data, not Agent model memory or a vector database.
