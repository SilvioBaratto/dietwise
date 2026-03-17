# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DietLogo AI — an Italian-language web app that generates personalized weekly meal plans using AI (BAML/LLM). Users set goals (weight, height, dietary preferences), the AI generates a weekly diet with recipes and grocery lists. Positioned as a wellness tool, not a medical device (see `law_diet.md` for regulatory context).

## Repository Structure

Two **separate git repositories** live under this workspace:

```
api/        # Backend — FastAPI, SQLAlchemy, BAML (own .git, deployed to Fly.io)
frontend/   # Frontend — Angular 20, Tailwind 4 (own .git, deployed to Vercel)
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
- Auth: Supabase OAuth (Google) with PKCE flow; JWT validated server-side
- Production API URL is relative (`/api/v1`), dev points to `localhost:8000`

### Backend (FastAPI)
```
Route (api/v1/*.py) → Service (services/*.py) → Repository (repositories/*.py) → SQLAlchemy Models
                        ↓
                      BAML Functions (baml_src/*.baml) → LLM (diet generation)
```
- Sync SQLAlchemy with psycopg2-binary (String IDs, not UUID objects)
- `baml_client/` is auto-generated — never edit manually, only edit `baml_src/`
- Auth: Supabase JWT via HTTPBearer, user auto-created in local DB on first auth

### Frontend (Angular 20)
- Standalone components only (no NgModules), OnPush change detection everywhere
- Signals for local state, RxJS Observables for cross-component auth state
- HTTP interceptor adds Bearer token, handles 401 refresh and 403 redirect
- Lazy-loaded routes with functional AuthGuard

## Commands

### Backend (run from `api/`)
```bash
uvicorn app.main:app --reload --port 8000    # Dev server
alembic upgrade head                          # Apply migrations
alembic revision --autogenerate -m "desc"     # New migration
pytest                                        # All tests
pytest -k "test_name"                         # Single test
fly deploy --app api-diet                     # Deploy to Fly.io
```

### Frontend (run from `frontend/`)
```bash
ng serve                                      # Dev server (localhost:4200)
ng build                                      # Production build
ng test                                       # Unit tests (Karma)
```

### BAML
```bash
# Edit baml_src/*.baml → VSCode extension auto-regenerates baml_client/
# Manual: run BAML CLI from api/ directory
```

## Code Rules

- Functions: max 50 lines. Files: max 500 lines.
- Backend IDs: always `String` type, never `UUID` objects (Supabase compatibility)
- Frontend: use `input()`/`output()` functions, not decorators. Use `inject()`, not constructor DI. Native control flow (`@if`, `@for`), not structural directives.
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
- Key vars: `SUPABASE_DB_URL`, `SUPABASE_URL`, `SUPABASE_KEY`, `MY_OPENAI_KEY`
- Python: conda env `fantacreator`, formatter: black. TypeScript: formatter: prettier.
