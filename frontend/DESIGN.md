# Design

The visual standard for the app. Read this before any UI work. The frontend reviewer checks screenshots against it; breaking it is blocking.

**Dark theme only in v1.** Don't build a light theme.

## Already built: reuse these

Run the app and open `/styleguide` (development only) to see them. Add new shared pieces there too.

| Need                                              | Use                                                                        |
| ------------------------------------------------- | -------------------------------------------------------------------------- |
| Tokens                                            | `src/styles/tokens.css`, mapped in `src/index.css`                         |
| Top bar, page width, canvas with side panels      | `AppShell`, `PageContainer`, `Workspace` in `src/components/app-shell.tsx` |
| Bento tiles and live numbers                      | `BentoGrid`, `Tile`, `Metric` in `src/components/bento.tsx`                |
| Health of anything                                | `StatusIndicator` and `statusFromUtilisation` (`src/lib/status.ts`)        |
| Loading, empty, error                             | `LoadingTiles`, `EmptyState`, `ErrorState` in `src/components/states.tsx`  |
| Aurora                                            | `Aurora`                                                                   |
| Canvas on a small screen                          | wrap the view in `LargeScreenOnly`                                         |
| Buttons, inputs, dialogs, menus, tooltips, toasts | `src/components/ui/` (shadcn)                                              |

In shadcn class names, "accent" means a hover surface. The violet `--accent` token is `bg-primary` / `text-primary`.

## Principle: functionalist minimalism

Form follows function. Every element must earn its place by helping the user build, run or understand a design. If removing something loses nothing, remove it.

- No decoration inside the product. Atmosphere (aurora) lives only on the landing page, sign-in and empty states.
- Show data, not chrome: borders and labels are quiet, numbers and status are loud.
- One primary action per screen. Secondary actions are ghost buttons or in menus.
- Prefer text and icons over illustrations. No stock imagery, no mascots.
- Density over padding in tool screens (canvas, results, admin); more breathing room on marketing screens (landing, sign-in).
- Consistent over clever: reuse existing patterns before inventing new ones.

## Look and feel

- **App shell: Orca-like.** A quiet, pane-based tool: a slim top bar, panels that dock to the sides, and the workspace filling everything else. Chrome is muted and recedes so the user's work is the brightest thing on screen.
- **Canvas: Excalidraw-like.** A calm, dark, infinite canvas with a minimal floating toolbar, keyboard shortcuts and nothing in the way. The canvas is for the user's design; chrome stays out of it.
- **Around the canvas: bento, with aurora only on the edges of the product.** Content is laid out in bento grids: rounded tiles of different sizes, each showing one thing. Soft aurora glows (blurred violet, indigo and blue gradients) appear only on the landing page, sign-in and empty states.

Colour has two jobs only: aurora for atmosphere, status colours for meaning. Never mix them. Status colours never appear in decoration, and aurora colours never signal health.

## Colour tokens

Define as CSS variables in `src/styles/tokens.css` and map them in Tailwind. Never use raw hex values in components.

| Token              | Value     | Use                                                                        |
| ------------------ | --------- | -------------------------------------------------------------------------- |
| `--bg`             | `#0B0D12` | App and canvas background                                                  |
| `--canvas-dot`     | `#1C2130` | Canvas dot grid                                                            |
| `--surface`        | `#12151D` | Bento tiles, panels                                                        |
| `--surface-raised` | `#181C26` | Modals, popovers, nodes                                                    |
| `--border`         | `#252A37` | Tile and node borders                                                      |
| `--text`           | `#E6E8EE` | Primary text                                                               |
| `--text-muted`     | `#8B92A5` | Secondary text, labels                                                     |
| `--accent`         | `#8B7CFF` | Primary buttons, focus rings, selection. Text on it is `--bg`, never white |
| `--aurora-1`       | `#7C5CFF` | Aurora glow (violet)                                                       |
| `--aurora-2`       | `#4F6BFF` | Aurora glow (indigo)                                                       |
| `--aurora-3`       | `#38BDF8` | Aurora glow (sky blue)                                                     |

### Status colours (meaning only)

| Token    | Value     | Meaning                                           |
| -------- | --------- | ------------------------------------------------- |
| `--ok`   | `#34D399` | Healthy, under ~70% utilisation, challenge passed |
| `--warn` | `#FBBF24` | Under strain, ~70–90% utilisation, queue building |
| `--bad`  | `#F87171` | Overloaded, errors, timeouts, challenge failed    |
| `--idle` | `#5B6275` | No traffic, disabled                              |

Status is never shown by colour alone: pair it with an icon or label (check, warning triangle, cross) so it works for colour-blind users.

## Aurora: where and how

- Use on: landing page hero, sign-in page, empty states. Nowhere else.
- Never on the canvas, results, challenge list, admin or account pages. Those are tool screens and stay purely functional.
- Built from 2–3 large blurred radial gradients (`blur(80–120px)`, 15–30% opacity) behind content, never behind text without a solid surface on top.
- Slow drift animation allowed (20s+ loop), disabled with `prefers-reduced-motion`.

## Bento grids

- CSS grid, 12 columns, `gap: 16px`. Tiles span different sizes to show importance (e.g. the main metric spans 6 columns, minor ones 3).
- Tile: `--surface`, 1px `--border`, `rounded-2xl`, `p-6` (`p-4` on tool screens). Aurora glow only inside landing-page hero tiles.
- One idea per tile: a title (`text-muted`, small), the content, optional action.
- Use bento for: landing page, dashboard/home, challenge list (cards sized by featured/difficulty), run results (verdict tile + metric tiles + "what broke" tile), account page.

## Typography

- UI: Inter. Metrics and numbers: JetBrains Mono (tabular figures, so live numbers don't jitter).
- Scale: 12 (labels), 14 (body), 16 (emphasis), 20 (tile titles), 28 (page titles), 48–56 (landing hero only).
- Weights: 400 body, 500 labels, 600 headings. No bold paragraphs.

## Canvas

- Dot grid background, pan and zoom, snap to grid.
- **Toolbar:** floating, top centre, icon buttons with tooltips and shortcut hints.
- **Component palette:** floating panel on the left, searchable, grouped as in [ADR 0001](../docs/adr/0001-product-scope-and-initial-decisions.md): traffic and entry, compute, data, messaging and processing, coordination.
- **Config panel:** slides in from the right when a node is selected.
- **Traffic:** entered as daily active users and requests per user, showing the resulting requests per second, which can be overridden.
- **Run controls + live metrics:** floating bar at the bottom: Run / Stop (there is no pause), traffic control with an RPS slider, incident trigger, then compact live metrics (p50, p95 and p99 latency, error rate, throughput) in JetBrains Mono.
- **Primary action:** on a challenge, Submit is primary and Run is secondary. In a free design, Run is primary.
- **Nodes:** `--surface-raised`, `rounded-xl`, 1px border, icon + name + one key metric. During a run the border and a small status dot take the status colour. Overloaded nodes pulse gently (1.5s), failed nodes stay solid `--bad`.
- **Edges:** thin `--idle` lines with arrowheads (`--border` is too faint to see); label shows protocol/API type. During a run, edges carry moving particles.
- **Icons:** `lucide-react`, one consistent icon per component type, 18px.

## Animation

- Request particles flow along edges; density reflects load (aggregated, not one particle per request). Particles on failing edges turn `--bad` and fade.
- Only animate things that carry data or feedback. No decorative motion inside the canvas.
- Durations: 150ms for UI feedback, 200–300ms for panels, never over 400ms except aurora drift.
- Respect `prefers-reduced-motion`: replace particles with a static load indicator on each edge.

## Components

- Build on shadcn/ui + Tailwind. Don't hand-roll buttons, inputs, dialogs, dropdowns, tooltips or toasts.
- Buttons: primary (`--accent`), secondary (surface + border), ghost (toolbar).
- Toasts for run events (started, stopped, finished, timed out, crashed, connection lost).
- Every view has loading (skeleton tiles), empty (short message + one action, aurora allowed) and error states.

## Layout

- The canvas needs a window at least 1280px wide; narrower screens see a "use a larger screen" message.
- Every other page works on phones: tiles stack and nothing scrolls sideways.
- Canvas pages are full-bleed; everything else is centred, max width 1200px.
- Spacing scale: 4, 8, 12, 16, 24, 32, 48. Nothing in between. This governs our layouts; the padding built into shadcn components stays as shipped.

## References

Open with Playwright for inspiration only. Never copy code, assets or exact designs.

- Orca (<https://github.com/stablyai/orca>, and its docs site): pane-based app shell, quiet chrome.
- Excalidraw (<https://excalidraw.com>): canvas feel, minimal floating toolbar.

For aurora and bento, follow the sections above and `/styleguide`; don't search for examples.
