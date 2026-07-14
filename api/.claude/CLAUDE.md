# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

- **Backend**: FastAPI (pinned in `requirements.txt`/`pyproject.toml`)
- **Database**: **Supabase-hosted PostgreSQL** — not local, not Docker. Connected via `SUPABASE_DB_URL`.
- **ORM**: SQLAlchemy 2.0 (synchronous), driver `psycopg2-binary`. An `async_database_url` property exists on `Settings` (`app/config.py`) but is dead code — no `asyncpg` engine is ever constructed anywhere in the app.
- **Migrations**: Alembic, run via `alembic/env.py`
- **AI/LLM**: BAML (`baml_src/*.baml` → generated `baml_client/`)
- **Validation**: Pydantic Settings v2 (`app/config.py`)
- **Server**: Gunicorn + Uvicorn workers in production (`docker/Dockerfile:105` — `CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]`); `uvicorn app.main:app --reload` for local dev.
- **Deployment**: Fly.io, app `api-diet`, region `fra`. `docker/Dockerfile` builds the deploy image — there is **no `docker-compose.yml`** anywhere in this repo, and no local Postgres container. `fly.toml`'s `release_command` runs `python -m alembic upgrade head` before every deploy.

## Architecture

### Directory Structure
```
app/
├── main.py                 # FastAPI app factory, lifespan, middleware wiring, health/docs/metrics endpoints
├── config.py                # Pydantic Settings v2 configuration
├── database.py               # DatabaseManager: sync SQLAlchemy engine, dynamic pool class, get_db()
├── dependencies.py            # RateLimiter (per-endpoint), DBSession alias, pagination/filter helpers
├── exceptions.py               # Custom exception hierarchy + global exception handlers
├── auth/
│   ├── supabase_auth.py          # SupabaseAuthManager — Supabase client + JWKS-based JWT verification
│   └── dependencies.py            # FastAPI auth dependencies — get_current_user, require_admin, user-sync-on-login
├── api/v1/                        # API endpoints
│   ├── router.py                    # Aggregates settings/diet/meal/recipe/admin/api_keys routers
│   ├── admin.py, settings.py, diet.py, meal.py, recipe.py, api_keys.py
├── models/                         # SQLAlchemy models (Base in base.py)
│   ├── base.py                       # Base, TimestampMixin, UUIDPrimaryKeyMixin/StringUUIDPrimaryKeyMixin (unused by real models)
│   ├── diet.py                        # User, WeeklyDiet, Meal, Ingredient, MealIngredient, GroceryList, GroceryListItem, SavedRecipe, UserSettings
│   └── api_key.py                      # UserApiKey (BYOK, AES-256-GCM encrypted)
├── schemas/                         # Pydantic request/response models
├── repositories/                     # Data-access layer (Repository pattern)
├── services/                          # Business-logic layer
│   ├── user_service.py, diet_service.py, meal_service.py
│   ├── api_key_service.py, api_key_validation_service.py, key_rotation_service.py
│   ├── encryption_service.py           # AES-256-GCM for BYOK keys
│   └── baml_client_factory.py          # Per-user BAML client builder — see BYOK section below
└── middleware/                       # Security, logging, rate limiting

baml_src/                 # BAML LLM function definitions
├── diet.baml            # GeneraDietaSettimanale, GeneraListaSpesa, ModificaDietaSettimanale, GeneraRicetta
├── clients.baml         # Static dev/test LLM clients (OpenAI/Gemini/Anthropic) + retry policies — overridden per-user in production, see BYOK section
└── generators.baml      # Python/Pydantic code generation config

baml_client/             # Auto-generated BAML Python client (DO NOT EDIT)
alembic/                 # Database migrations (alembic/env.py, alembic/versions/)
```

Note: no `websockets/` directory exists. No `tests/` directory exists either — see Testing below.

### Data Flow Pattern
1. **Route** (`api/v1/*.py`) → validates request with Pydantic schemas, resolves the authenticated user via `Depends(get_current_user)` (or `AdminUser`/`OptionalUser`)
2. **Service** (`services/*.py`) → orchestrates business logic, owns the transaction boundary (commits), calls repositories and/or BAML functions
3. **Repository** (`repositories/*.py`) → handles database reads/writes; flushes but never commits — commit ownership belongs to the service
4. **BAML Functions** → type-safe LLM calls for diet generation, recipes, grocery lists, invoked through `BamlClientFactory` for per-user BYOK

### Database Architecture
- **Connection**: Synchronous engine, `psycopg2` driver, `sslmode=require` always, `application_name=f"api-diet-{settings.environment}"` (`app/database.py`).
- **Pooling**: **Not** a flat QueuePool. `_get_optimal_pool_class()` (`database.py`) picks `NullPool` if the configured URL targets Supabase's transaction pooler (port `6543`) or `settings.is_development` is true; otherwise `QueuePool`. Pool sizing when `QueuePool` is active: `pool_size=15`, `max_overflow=3`, `pool_timeout=10`, `pool_recycle=300` (5 min), `pool_pre_ping=True` — these match `fly.toml`'s `[env]` overrides exactly (no drift between code defaults and production config).
- **Session Pattern**: Context manager via `get_db()` dependency, wraps `DatabaseManager.get_session()`.
- **ID Strategy**: String IDs (not UUID objects) — see Critical Rules.
- **Models**: User → WeeklyDiet → Meals → MealIngredients, GroceryList. Also `UserSettings`, `SavedRecipe`, `UserApiKey`.
- **Migrations**: `alembic/env.py` prefers `DIRECT_DATABASE_URL` (non-pooled, for DDL/prepared statements) and falls back to `SUPABASE_DB_URL` if unset — see Configuration below.

## Commands

### Local Development
```bash
uvicorn app.main:app --reload --port 8000    # Dev server (requires a valid .env — see Configuration)
python -m app.main                            # Equivalent, via the __main__ block
pip install -r requirements.txt               # Install dependencies
```

There is no Docker-based local dev flow — the app connects to hosted Supabase Postgres directly, in every environment.

### Database Migrations
```bash
alembic upgrade head                          # Apply migrations
alembic revision --autogenerate -m "desc"     # New migration
alembic downgrade -1                          # Rollback one migration
alembic history                               # View migration history
alembic upgrade head --sql                    # Offline dry-run — emits SQL without connecting, safe for verifying env.py changes
```

### BAML
```bash
# Edit baml_src/*.baml → VSCode extension auto-regenerates baml_client/
# Manual: baml-cli generate (run from api/)
```

### Testing
`pyproject.toml` configures `testpaths = ["tests"]` under `[tool.pytest.ini_options]`, but **no `tests/` directory currently exists in `api/`** — running `pytest` today collects zero tests. This is a known gap, not a documented working command; treat any pre-existing "run tests" instructions with suspicion until a real `tests/` tree is added.

## Configuration

### Environment Variables
- Loaded via Pydantic Settings v2 (`app.config.Settings`), from a `.env` file (no `.env.example` currently checked in).
- **Required** (app fails to start without these — no defaults):
  - `SUPABASE_DB_URL` — Postgres connection string (app runtime + migration fallback)
  - `SUPABASE_URL` — Supabase project URL
  - `SUPABASE_KEY` — Supabase anon/service key, used to construct the auth client
  - `API_KEY_ENCRYPTION_SECRET` — base64-encoded 32-byte AES-256-GCM key for BYOK key encryption (`EncryptionService`)
- **Optional**:
  - `DIRECT_DATABASE_URL` — non-pooled Postgres connection, used **only** by Alembic migrations. Falls back to `SUPABASE_DB_URL` if unset. Use Supabase's *Direct connection* string (port 5432) here, not the Transaction Pooler (port 6543) — the pooler doesn't reliably support the prepared statements/DDL Alembic issues. `alembic/env.py` logs which one is active (host/port only, credentials redacted) on every migration run.
  - `DEBUG`, `ENVIRONMENT` (`development`|`production`), `REDIS_URL`, `SWAGGER_USER`/`SWAGGER_PASS` (gates `/docs`/`/redoc` in production), `DEV_AUTH_BYPASS`, rate-limit/cache/log-level settings — see `app/config.py` for full list and defaults, don't assume values not read directly from that file.
- **Not** a `Settings` field, read directly by BAML at runtime: `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY` — consumed by `baml_src/clients.baml`'s static dev/test clients (`env.OPENAI_API_KEY` etc). These are separate from the per-user encrypted BYOK keys stored in `UserApiKey` rows and decrypted by `EncryptionService` — there is no `MY_OPENAI_KEY` variable anywhere in this codebase.
- There is no `JWT_SECRET_KEY` anywhere in the codebase — JWT verification is delegated entirely to the Supabase SDK's JWKS-based `get_claims()` (see Authentication below), not a locally-held signing secret.

## Authentication & Authorization

- **Supabase JWT via `HTTPBearer`**, verified through **cached JWKS-based signature verification** (`app/auth/supabase_auth.py`, `SupabaseAuthManager.validate_jwt_claims()` → `client.auth.get_claims(jwt=token)`). This is a **local** verification path — the JWKS keyset is fetched once and cached by the SDK, so per-request auth does **not** round-trip to Supabase's Auth API. After signature verification, the code additionally checks `exp`, `iss` (must equal `{SUPABASE_URL}/auth/v1`), `aud` (must equal `"authenticated"`), and `role`.
- A slower path (`get_user_from_token()`, real network call to Supabase) exists but is not used by the standard auth dependency chain — it's only reachable via `validate_token(token, require_fresh=True)`, which nothing in this codebase currently calls.
- **Dependency chain** (`app/auth/dependencies.py`): `get_current_user_from_token` (validates JWT, syncs/creates local `User` row) → `get_current_user` (adds `is_approved`/`is_admin` gating — non-admins pending approval get 403) → `require_admin` (403 if not admin). Also `get_optional_user` (swallows auth errors, returns `None`) and `get_user_id`. Type aliases used by routers: `CurrentUser`, `OptionalUser`, `AdminUser`, `RequireAuth`, `UserId`.
- **User sync-on-first-auth**: on every successful JWT validation, `get_current_user_from_token` looks up a local `User` row by Supabase `sub` (ID) OR email. If neither matches, it inserts a new `User(id=user_id, email=email)` — auto-provisioning on first login, no separate signup step. If a row matches by email but has a **different** ID (e.g. the user's Supabase `auth.users.id` changed), the code does **not** rewrite the local row's ID — it logs a warning and keeps using the existing local user, to avoid orphaning that user's diets/meals/settings (all FK'd to `users.id`). This means the response's `id` field can differ from the JWT's `sub` claim in that scenario — a known, deliberate behavior, not a bug.
- Anonymous Supabase auth users are explicitly rejected.
- 401s (missing header, invalid/expired token, anonymous user) go through the custom `AuthenticationError` exception → its handler adds `WWW-Authenticate: Bearer` + `X-Auth-Error` headers. 403s for "pending approval" and "admin required" are raised as plain `HTTPException(403)` rather than the custom `AuthorizationError` class, so they get the generic error envelope, not the enriched one — a known inconsistency, not something to silently "fix" without checking both call sites.

## BYOK (Bring Your Own Key) / BAML Architecture

This is one of the more distinctive subsystems in this codebase — every diet/recipe/grocery-list generation call uses the **calling user's own** LLM API key, not a shared server key.

- `baml_src/clients.baml` declares static `OpenAI`/`Gemini`/`Anthropic` clients reading `env.OPENAI_API_KEY` etc. — these are **dev/test defaults only**. In production, `BamlClientFactory` (`app/services/baml_client_factory.py`) overrides the primary client per-request via a runtime `baml_py.ClientRegistry()`.
- `BamlClientFactory._build_client()`: reads the user's `UserSettings.preferred_provider`/`preferred_model`, fetches their encrypted `UserApiKey` row, decrypts it (`EncryptionService`, AES-256-GCM), and registers it as `ClientRegistry`'s primary client. Raises `ApiKeyNotConfiguredError` if the user hasn't configured a provider/key.
- `EncryptionService` (`app/services/encryption_service.py`): AES-256-GCM, key derived from `API_KEY_ENCRYPTION_SECRET` (must base64-decode to exactly 32 bytes). On decrypt failure (`InvalidTag` — e.g. the encryption secret was rotated without re-encrypting existing rows), `BamlClientFactory` catches it, invalidates the stored key, and returns an actionable `LLM_KEY_INVALID` error rather than a generic 502.
- `BamlClientFactory.handle_baml_error()` classifies raw provider exceptions by string-matching: 401/unauthorized → invalidate key + `LLM_KEY_INVALID`; 429/rate limit → `RateLimitError`; quota/billing → `LLM_QUOTA_EXCEEDED`; model-not-found → `LLM_MODEL_UNAVAILABLE`; anything else → generic `LLMProviderError`.
- `key_rotation_service.py` / `api_key_validation_service.py` handle key rotation and provider-side key validation respectively.

## Commands (BAML function usage)
```python
from baml_client import b  # Generated client — do NOT use directly for user-facing generation, see BamlClientFactory above

# Type-safe LLM function call (dev/test path, uses static clients.baml clients)
result = b.GeneraDietaSettimanale(
    dataInizio="2025-01-01",
    peso=70.0,
    altezza=175.0,
    obiettivo="lose weight",
    altri_dati="vegetarian"
)
```
In production code paths (`DietService`, `MealService`), always go through `self._baml.get_client()` (a `BamlClientFactory` instance), not the bare `b` import — that's what makes the call BYOK-scoped.

## Code Patterns

### Database Session
```python
from app.database import get_db

def endpoint(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == "123").first()
```

### Repository Pattern
```python
class DietRepository(BaseRepository[WeeklyDiet, DietSummary, DietSummary]):
    def get_by_user_id(self, user_id: str) -> list[WeeklyDiet]:
        return self.db.query(WeeklyDiet).filter(
            WeeklyDiet.user_id == user_id
        ).all()
```
Not every repository extends `BaseRepository` — some (`UserRepository`, `MealRepository`, etc.) are plain hand-written classes. All follow the same convention: `db.add()` + `db.flush()`, never `db.commit()` — commit ownership belongs to the calling service.

### Error Handling
- Custom exception hierarchy rooted in `BaseAPIException` (`app/exceptions.py`) — `ValidationError`, `AuthenticationError`, `AuthorizationError`, `NotFoundError`, `ConflictError`, `RateLimitError`, `ExternalServiceError`, `DatabaseError`, plus BYOK-specific `ApiKeyNotConfiguredError` and `LLMProviderError`.
- Global exception handlers registered via `setup_exception_handlers(app)` in `main.py`.
- Standard error envelope: `{"error": {"code", "message", "timestamp", "details", "request_id"}}`.

## Critical Rules

### IDs and Types
- **CRITICAL**: Use `String` type for IDs, NOT `UUID`. All real models (`User`, `WeeklyDiet`, `Meal`, etc.) hand-roll a plain `String` primary key — `app/models/base.py` also defines `UUIDPrimaryKeyMixin`/`StringUUIDPrimaryKeyMixin`/`BaseModel` mixins, but **no concrete model uses them**; treat that as unused scaffolding, not the pattern to follow.
- `User.id` specifically is populated from the Supabase JWT's `sub` claim (a string), not app-generated — do not `str(uuid.uuid4())` it.
- **Rationale**: prevents UUID type mismatch errors against Supabase.

### BAML Files
- Edit only files in `baml_src/`. Never manually edit `baml_client/` (auto-generated).
- After editing `.baml` files, regenerate: `baml-cli generate` (or let the VSCode extension do it).
- Remember `clients.baml`'s static clients only affect the dev/test path — production traffic goes through `BamlClientFactory`'s per-user `ClientRegistry` override (see BYOK section).

### Database Migrations
- Never edit migration files manually after creation. Always use `alembic revision --autogenerate`, review before applying.
- `alembic/env.py` prefers `DIRECT_DATABASE_URL` over `SUPABASE_DB_URL` — if you're debugging a migration that behaves differently locally vs. in CI/Fly, check which one is actually active (logged at migration start).
- `alembic.ini`'s `sqlalchemy.url` must stay a placeholder (`driver://user:pass@localhost/dbname`) — the real URL only ever comes from environment variables via `env.py`. Never commit a real connection string there.

### Connection Pooling
- Pool class is chosen dynamically (`NullPool` for the Supabase transaction pooler or dev mode, `QueuePool` otherwise) — don't assume a flat "always QueuePool."
- Production values: pool size 15, max overflow 3, recycle 300s, pre-ping enabled.

### Auth Core
- `app/auth/` (`supabase_auth.py`, `dependencies.py`) is sensitive — don't modify without care (also flagged as do-not-modify-without-permission in the workspace-root `dietwise/CLAUDE.md`).

### Dependencies
- Do NOT add dependencies without updating `requirements.txt` (and `pyproject.toml` if touched — see workspace root for which manifest actually drives the Docker build).
- Keep versions pinned to specific releases (`==`), not open ranges — this repo pins to latest-at-time-of-update rather than floating `>=`.

## Middleware Stack

Registered in `app/main.py:create_application()`, in this order (first-added = outermost):
1. **CORS** — always added.
2. **RateLimitingMiddleware** — only if `settings.is_production_like` (skipped entirely in development).
3. **SecurityHeadersMiddleware** — always added.
4. **LoggingMiddleware** — added if `settings.debug` or `log_level` is `DEBUG`/`INFO` (true by default).

Actual request execution order: **CORS → RateLimiting → SecurityHeaders → Logging → routes**.

## API Structure

### Endpoints (all under `/api/v1`, from `app/api/v1/router.py`)
- `/api/v1/settings/*` — user settings CRUD
- `/api/v1/diet/*` — weekly diet CRUD + BAML-driven generation/modification
- `/api/v1/meal/*` — meal-level endpoints
- `/api/v1/recipe/*` — recipe generation/saved-recipe endpoints
- `/api/v1/api-keys/*` — BYOK API key management (save/list/delete/validate/preferences)
- `/api/v1/admin/*` — user approval/admin management

### Authentication
- Every substantive route is gated behind `Depends(get_current_user)` or `AdminUser` — this is **not** an open API. See Authentication & Authorization above for the full dependency chain.

### Response Format
- Success: 200/201 with data
- Validation errors: 422 with Pydantic error details
- Business logic errors: 400/404/409 with custom error messages
- Server errors: 500 with generic message (details in logs, not the response, unless `app.debug`)

## Common Tasks

### Adding a New Endpoint
1. Define Pydantic schema in `app/schemas/`
2. Create repository method in `app/repositories/`
3. Implement service logic in `app/services/` (own the commit)
4. Add route in `app/api/v1/` and register in `router.py`

### Adding a New BAML Function
1. Define classes and function in `baml_src/*.baml`
2. Regenerate `baml_client/` (`baml-cli generate` or VSCode extension)
3. If it needs to run BYOK, call it through `BamlClientFactory.get_client()`, not the bare `baml_client` import

### Modifying Database Schema
1. Edit SQLAlchemy models in `app/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review the generated migration file
4. Apply: `alembic upgrade head`

## Monitoring & Debugging

### Logs
- Configured in `app/main.py` via `logging.basicConfig()`. Level controlled by `LOG_LEVEL` env var (default `INFO`). Format: text (dev) or JSON (production, `LOG_FORMAT=json`).

### Health Endpoints
- `/health` — trivial liveness check.
- `/health/deep` — database, memory, disk, and Fly.io system info; returns 503 if any check fails.

### Metrics
- Prometheus metrics at `/metrics` (via `prometheus-client`).
- `/fly/system` — Fly.io-specific system info (region, machine ID, CPU/memory/disk).

### Documentation
- Swagger UI (`/docs`) / ReDoc (`/redoc`): unprotected in development, gated behind HTTP Basic auth (`SWAGGER_USER`/`SWAGGER_PASS`) in production, disabled entirely if those aren't set.
- `/openapi.json`: available in development or authenticated production.

## Security

### Never Commit
- `.env` file
- Real database credentials — including in `alembic.ini`'s `sqlalchemy.url`, which must stay a placeholder (see Database Migrations above; this rule exists because a real credential was previously committed there)
- API keys (per-user BYOK keys live encrypted in the DB, never in env vars or code)
- Generated `baml_client/` can be committed (deterministic output)

### BYOK Key Storage
- Per-user LLM API keys are encrypted at rest with AES-256-GCM (`EncryptionService`), keyed from `API_KEY_ENCRYPTION_SECRET`. See BYOK section above for the full decrypt-failure/key-rotation handling.
