# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DietLogo AI — an Italian-language web app that generates personalized weekly meal plans using AI (BAML/LLM). Users set goals (weight, height, dietary preferences), the AI generates a weekly diet with recipes and grocery lists. Positioned as a wellness tool, not a medical device (see `law_diet.md` for regulatory context).

## Repository Structure

Two **separate git repositories** live under this workspace:

```
api/        # Backend — FastAPI, SQLAlchemy, BAML (own .git, deployed to Fly.io)
frontend/   # Frontend — Angular 21, Tailwind 4 (own .git, deployed to Vercel)
```

## Context Loading Rules

- **Backend tasks** → Read `api/.claude/CLAUDE.md`
- **Frontend tasks** → Read `frontend/.claude/CLAUDE.md`
- **Full-stack tasks** → Read both
- **UI/styling tasks** → Also read `frontend/src/styles.css`

## Architecture

### Deployment Topology
```
Browser → Vercel (Angular SPA)
            ↓ /api/* rewrite (vercel.json)
          Fly.io (FastAPI) → Supabase PostgreSQL
            ↓
          BAML → OpenAI (diet/recipe generation)
```

- Frontend proxies `/api/*` requests to `https://api-diet.fly.dev/api/*` via Vercel rewrites
- Auth: Supabase OAuth (Google) with PKCE flow; JWT validated server-side (`api/app/auth/supabase_auth.py`)
- Production API URL is relative (`/api/v1`), dev points to `localhost:8000`
- CSP headers configured in `frontend/vercel.json` — must whitelist Supabase domains for `connect-src`

### Backend (FastAPI)
```
Route (api/v1/*.py) → Service (services/*.py) → Repository (repositories/*.py) → SQLAlchemy Models
                        ↓
                      BAML Functions (baml_src/*.baml) → LLM (diet generation)
```
- Sync SQLAlchemy with psycopg2-binary (String IDs, not UUID objects)
- `baml_client/` is auto-generated — never edit manually, only edit `baml_src/`
- Auth: Supabase JWT via HTTPBearer, user auto-created in local DB on first auth
- Middleware stack (order matters): SecurityHeaders → Logging → RateLimiting → CORS

### Frontend (Angular 21)
- Standalone components only (no NgModules), OnPush change detection everywhere
- Signals for local state, RxJS Observables for cross-component auth state
- HTTP interceptor adds Bearer token, handles 401 refresh and 403 redirect
- Lazy-loaded routes with functional AuthGuard

## CI/CD

GitHub Actions workflows are **path-scoped** — only trigger when files in their respective directory change:

- **`frontend.yml`** — on push/PR to `main` with `frontend/**` changes: build → test → deploy (preview on PR, production on merge)
- **`deploy-backend.yml`** — on push to `main` with `api/**` changes: deploys to Fly.io
- **`ci-backend.yml`** — on push/PR to `main` with `api/**` changes: lint (ruff + black) → test (pytest) → docker build

Fly.io runs `alembic upgrade head` as a release command before each deployment (configured in `fly.toml`).

Required GitHub Secrets: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `FLY_API_TOKEN`

## Commands

### Backend (run from `api/`)
```bash
uvicorn app.main:app --reload --port 8000    # Dev server
alembic upgrade head                          # Apply migrations
alembic revision --autogenerate -m "desc"     # New migration
pytest                                        # All tests
pytest -k "test_name"                         # Single test
ruff check .                                  # Lint
black --check .                               # Format check
black .                                       # Auto-format
fly deploy --app api-diet                     # Deploy to Fly.io
```

### Frontend (run from `frontend/`)
```bash
ng serve                                      # Dev server (localhost:4200)
ng build --configuration production           # Production build
ng test --watch=false --browsers=ChromeHeadless  # Unit tests (CI-compatible)
ng test                                       # Unit tests (interactive)
```

### BAML
```bash
# Edit baml_src/*.baml → VSCode extension auto-regenerates baml_client/
# Manual: run BAML CLI from api/ directory
```

## Code Rules

- Functions: max 50 lines. Files: max 500 lines.
- Backend IDs: always `String` type, never `UUID` objects (Supabase compatibility)
- Frontend: use `input()`/`output()` functions, not decorators. Use `inject()`, not constructor DI. Native control flow (`@if`, `@for`), not structural directives. `standalone: true` is the default — do NOT set it explicitly.
- Update the relevant README.md after making changes (no new .md files)

## Do NOT Modify Without Permission
- Test files (`*.spec.ts`, `test_*.py`)
- Migration files (use Alembic to generate new ones)
- `baml_client/` (auto-generated)
- Build configs (`angular.json`, `fly.toml`)
- Auth core (`api/app/auth/`)

## Environment

- Backend env: `.env.dev` / `.env.prod` at workspace root (loaded via Pydantic Settings)
- Frontend env: `frontend/src/environments/environment.ts` (dev) / `environment.prod.ts` (prod)
- Key vars: `SUPABASE_DB_URL`, `SUPABASE_URL`, `SUPABASE_KEY`, `API_KEY_ENCRYPTION_SECRET`, `OPENAI_API_KEY` (optional fallback)
- Fly.io secrets (set via `fly secrets set`): `API_KEY_ENCRYPTION_SECRET`, `SUPABASE_DB_URL`, `SUPABASE_URL`, `SUPABASE_KEY`
- Python: conda env `fantacreator`, linter: ruff, formatter: black. TypeScript: formatter: prettier.
