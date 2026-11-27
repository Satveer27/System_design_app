# Backend and pipeline

The FastAPI API in `backend/` and the Airflow jobs in `pipeline/`. Read the root `CLAUDE.md`
first. If this file conflicts with an ADR, the ADR wins. Say so on the issue.

## Stack
- Python 3.13, FastAPI, Pydantic v2
- SQLAlchemy 2.0 async + asyncpg, Alembic migrations, PostgreSQL (RDS in production)
- Redis for sessions and rate limits
- Airflow 3 (LocalExecutor) for scheduled jobs; boto3 for S3
- Phase 2: MLflow for experiment tracking and model versions
- uv for dependencies (`uv add <pkg>`, never pip)
- pytest + pytest-asyncio, hypothesis, ruff, mypy (strict), bandit

## Layout
```
backend/
  app/
    main.py            # app factory, routers, middleware
    config.py          # settings from .env (pydantic-settings); add new ones to .env.slot.example
    db.py              # Base, async engine and session
    api/               # routers only: parse request, call service, return schema
    schemas/           # Pydantic request/response models = the API contract
    services/          # business logic, no FastAPI imports
    models/            # SQLAlchemy models
    auth/              # Google sign-in, email links, server-side sessions
    fpl/               # FPL API client and response parsing (shared with pipeline/)
    rules/             # FPL rules: squad validity, transfer cost, points calculator
  migrations/          # Alembic
  tests/
    unit/              # services and rules, no DB
    api/               # endpoint tests with httpx AsyncClient
pipeline/
  dags/                # Airflow DAGs: daily sync, pre-deadline, post-gameweek, backfill
  tasks/               # plain Python functions the DAGs call, tested without Airflow
```

## API rules
- Routers stay thin. Logic goes in `services/`, FPL rules in `rules/`.
- Every route is under `/api`. Every endpoint has Pydantic request and response models in
  `schemas/` matching the issue's API contract exactly. Keep the OpenAPI schema accurate: the
  frontend generates its types from it.
- All DB access is async. No raw SQL built from strings.
- Errors: raise domain exceptions in services, map them to HTTP errors in one handler. Never
  return stack traces to clients.
- Every endpoint that changes data checks the current user owns it.
- The API never calls FPL during a request, except to import a manager's squad. Imported squads
  are stored for the gameweek and reused.

## Auth and accounts
- Sign-in with Google or an emailed one-time link. No passwords.
- Sessions live server-side in Redis; the browser gets an opaque session ID in an `HttpOnly`,
  `Secure`, `SameSite=Lax` cookie. Rotate the ID on sign-in.
- CSRF token required on every state-changing request.
- Email links are single-use, expire, and are stored hashed. Requesting one never reveals whether
  an account exists. Auth endpoints are rate-limited. Email is sent outside the request.
- Stored per user: email, username, Google account ID if used, optional FPL team ID, Plans, tier
  lists, favourites. Account deletion removes all of it and is covered by a test.
- A shared tier list link is read-only and exposes nothing else about its owner.

## FPL rules
- `rules/` is pure Python with no I/O. Squad validity: 15 players (2 GK, 5 DEF, 5 MID, 3 FWD),
  budget, at most three per club, valid starting formation, captain and vice-captain.
- Transfers are counted against the imported squad; extra transfers cost 4 points each. Chips are
  ignored in v1.
- The points calculator is tested against FPL's own `explain` breakdowns from stored gameweeks.

## Pipeline rules
- Call FPL only from `fpl/`, with a browser-style User-Agent and a few requests per run. Use
  `/event/{gw}/live/` for gameweek stats, not one request per player.
- Save every FPL response unchanged to S3 before parsing it. Clean tables are rebuilt from S3.
- Check the shape of each response. If fields are missing or renamed, fail the task and alert on
  Discord. Never save partial or guessed data.
- Every task is safe to rerun: running it twice gives the same result and no duplicates.
- Jobs read deadlines and gameweek status from the database, not fixed times. Results are read
  only after FPL marks the gameweek finished and checked.
- Handle double and blank gameweeks: a player may have two fixtures or none.
- FPL's expected points (`ep_next`) are saved before every deadline from phase 1 onwards.
- Failures, shape changes and missed pre-deadline jobs alert on the Discord webhook.

## ML rules (phase 2)
- Every training run is logged in MLflow with its data window, features, parameters and scores.
- Test only walk-forward: train on earlier gameweeks, test on later ones. Never shuffle.
- Never use the historical `xP` column: it was recorded after matches.
- Features use only data available before that gameweek's deadline.
- A retrained model replaces the current version only if it scores better on the walk-forward
  test.
- Predictions are made in the pre-deadline job, then locked. Never change a locked prediction.

## Testing
- Write the test first. Each acceptance criterion in the issue gets a test.
- Cover edge cases: empty input, limits, invalid data, unauthorised and wrong-owner access, failure
  paths. Not just the happy path.
- Don't mock the thing under test. Mock only external services (FPL, S3, email, Google).
- FPL responses in tests come from stored real responses in `tests/fixtures/`, not invented data.
- API tests run against the slot's database in a transaction that rolls back.

## Migrations
- Only with the `migrate` label and the lock. One migration per issue, always with a downgrade.
- New models must be imported by `migrations/env.py`.
- Run `uv run alembic upgrade head` against your slot's DB and run tests after.

## Not set up yet
Everything: the first tickets create the project, Docker setup, Airflow, S3 access and CI.
