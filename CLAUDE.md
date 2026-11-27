# FPL Analytics

A free, non-commercial website for Fantasy Premier League managers: player and club analytics,
Plans built on a drag-and-drop pitch, shareable tier lists and, in phase 2, machine-learning
predictions with a public scorecard of how they performed. Data comes from FPL's unofficial API
(see `docs/adr/0001-use-the-unofficial-fpl-api.md`).

## Phases
- **Phase 1, data and analytics:** pipeline, analytics pages, Plans, tier lists, favourites,
  accounts. FPL's own expected points are saved before every deadline from the start.
- **Phase 2, ML:** match and stat predictors, points calculator, team of the week, scorecard,
  model history.
- **After launch:** challenger points model, live gameweek page, collaborative editing,
  mini-league roast.
Work only on the phase your issue belongs to.

## Repo layout
- `backend/`: FastAPI API. Has its own CLAUDE.md.
- `pipeline/`: Airflow jobs that load FPL data (and, in phase 2, train and predict). Rules are in
  `backend/CLAUDE.md`.
- `frontend/`: React + TypeScript site. Has its own CLAUDE.md.
- `docs/adr/`: decisions. `GLOSSARY.md`: domain terms. Read both before planning.
- `scripts/`: workflow tools (`agent_done.py`, `evidence.py`).

## Architecture
- FPL API → raw responses in S3 → clean tables in PostgreSQL (RDS in production) → API → site.
- Airflow on an Oracle server runs the daily sync, the pre-deadline job and the post-gameweek job.
- The website only reads stored data. It never calls FPL, except to import a manager's squad.
- Production: site on Vercel at the root domain, API at `api.` on the Oracle server behind Caddy.

## Commands
Not set up yet: the first tickets create them. Expected:
- Start local services: `docker compose up -d db redis`
- Backend: `cd backend && uv run uvicorn app.main:app --port $API_PORT`
- Backend checks: `cd backend && uv run pytest && uv run ruff check . && uv run mypy .`
- Frontend: `cd frontend && pnpm dev --port $WEB_PORT`
- Frontend checks: `cd frontend && pnpm lint && pnpm tsc --noEmit && pnpm test`
- Issues/PRs: use `gh` (`gh issue view N`, `gh pr create`)
- Git hooks (once per clone): `uv tool install pre-commit && pre-commit install`. Never skip them.

Ports, DB name and Redis DB come from the slot's `.env`. Never hardcode them.
Load it into the shell before running a server: `set -a; source .env; set +a`

## Non-negotiables
- Work on exactly one issue. Its acceptance criteria and API contract are the spec.
- Write tests first. A response shape in the issue must have a test proving it.
- Never merge, never push to main, never commit secrets.
- Only work on issues labelled `migrate` if you hold the migration lock.
- If something is unclear, comment on the issue and stop. Don't guess.
- HARD RULE: commit messages never include a `Co-Authored-By` line for Claude or any AI.
- HARD RULE: comments only say what the code does or how it works: short, stated as fact.
  Never justify a decision, give your reasons, argue that code is correct or safe, or describe a
  change: a made-up reason can mislead a reviewer. Remove such comments from code you touch.
  Reasons go in the PR description or an ADR. Tool directives such as `noqa` or `nosemgrep` may
  stay, without prose.

## Honesty rules
- Only report output from commands you actually ran in this session. Paste it
  verbatim. If you didn't run something, write "not run".
- Never claim tests pass, a bug is fixed, or a feature works without having run
  the check that proves it.
- Before using a function, class, endpoint or library API, confirm it exists by
  reading the code or the installed package's docs. Don't write code against an
  API you assume exists.
- Never add a dependency you haven't confirmed exists on PyPI/npm; justify each
  new dependency in the PR.
- If you're unsure, say so and ask on the issue. "I don't know" beats a guess.

## Agent skills

### Issue tracker
Issues and specs live in GitHub Issues. External PRs are not a request surface.
See `docs/agents/issue-tracker.md`.

### Triage labels
State labels, `backend`/`frontend` routing, a `migrate` lock and a two-attempt
review loop. See `docs/agents/triage-labels.md`.

### Domain docs
Domain terms are in `GLOSSARY.md`, and decisions in `docs/adr/`. Use glossary
terms exactly in code, tests and issues.
