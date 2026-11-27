# Frontend

React + TypeScript site: analytics pages, the Plan pitch, tier lists, favourites and accounts.
Read the root `CLAUDE.md` first. If this file conflicts with an ADR, the ADR wins. Say so on the
issue.

Before any UI work, read `DESIGN.md` in this folder. Its colour tokens, typography, components,
status colours and layout rules apply. Its **Canvas** and **Animation** sections describe a
previous project and are being rewritten: ignore them. Don't introduce new colours or styles.

Every page works on phones without sideways scrolling. The Plan pitch and tier list builder must
also be usable by touch.

## Stack
- React + TypeScript (strict), Vite
- React Router (route config in `src/routes.tsx`)
- TanStack Query for API data, Zustand for Plan and tier list editing state
- Tailwind and shadcn/ui, lucide-react icons, Inter and JetBrains Mono
- A drag-and-drop library for the pitch and tier lists, chosen in its ticket
- A chart library for player and club graphs, chosen in its ticket
- No automated frontend tests in v1 (see Testing)
- pnpm (never npm or yarn)

## Layout
```
frontend/src/
  api/          # generated API types + typed fetch functions, one per endpoint
  features/
    home/       # next deadline, top players, this gameweek's fixtures
    players/    # player table, player page with charts
    clubs/      # league table with movement, club form, fixture difficulty
    plans/      # Plan pitch builder, squad import, Best Squad
    tier-lists/ # tier list builder and shared view
    favourites/ # bookmarked players and clubs
    auth/       # Google and email-link sign-in, sign out
    account/    # settings, linked FPL team ID, account deletion
    legal/      # privacy page
    scorecard/  # phase 2: how the predictions performed
  routes.tsx    # all routes; protected routes wrapped in an auth guard
  components/   # shared UI; components/ui/ holds shadcn components
  styles/       # tokens.css, the only place for raw colour values
  stores/       # Zustand stores
  lib/          # utils
```

## API contract
- Types in `src/api/` are generated from the backend OpenAPI schema (`pnpm gen:api`). Never
  hand-write types for backend responses.
- `VITE_API_URL` is the API base. Leave it empty in dev to use the proxy.
- Only call endpoints that exist and are merged. If the issue needs one that doesn't, the issue
  is blocked: comment and stop.
- All fetches go through `src/api/`, never directly in components.
- Never call FPL from the browser.

## Sessions and auth
- Server-side sessions in an HttpOnly cookie; all requests use `credentials: "include"`.
- State-changing requests send the CSRF token; the fetch wrapper adds it.
- Never store tokens or session IDs in `localStorage` or `sessionStorage`.
- On a 401 from a protected page, redirect to sign-in keeping the return path. Public pages
  (analytics, shared tier lists, privacy, sign-in) never redirect.
- Account deletion asks for confirmation and explains what is deleted.

## Plans and tier lists
- Make every edit a discrete action in the store (add, remove, move, swap, set captain), so that
  collaborative editing can be added later.
- The pitch shows rule problems as they happen: budget, three per club, formation, squad size.
  Show each problem in words, not only colour.
- Saved state is visible: saving, saved, or failed with retry.

## Data display
- Prices are FPL game prices (for example £9.4m), never real transfer fees.
- Every page shows when its data was last updated.
- Phase 1 shows FPL's own expected points, labelled as FPL's. Phase 2 adds ours alongside.

## UI rules
- Every async view has loading, empty and error states.
- Never signal a state by colour alone: add an icon or a text label.
- Charts have a text alternative or data table.
- Keyboard accessible: real buttons, labelled inputs, visible focus. Drag and drop also works by
  keyboard.
- Keep components small. Logic in hooks, rendering in components.
- No new dependencies without saying why in the PR description.

## Browser (Playwright MCP)
- References: only sites named in the issue, 1-2 screenshots each. Take inspiration only: never
  copy their code, assets, logos, text or exact design.
- Self-check before opening a PR: walk through the acceptance criteria at
  `http://localhost:$WEB_PORT` and take screenshots at 1440px and 375px.

## Testing
- v1 has no automated frontend tests. The checks are lint, types, a production build, your
  self-check in the browser and the reviewer's screenshots.
- Rules a user relies on (budget, three per club, formation) are enforced and tested in the
  backend; the frontend shows the API's verdict, so its logic stays thin.

## Commands
- First run in a slot: `pnpm install`
- Dev: `pnpm dev --port $WEB_PORT`
- Checks: `pnpm lint && pnpm tsc --noEmit && pnpm build`
- Regenerate API types: `pnpm gen:api`

## Not set up yet
Everything: the first frontend ticket creates the project from these rules.
