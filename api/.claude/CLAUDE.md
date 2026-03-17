# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

- **Backend**: FastAPI 0.121.0+
- **Database**: PostgreSQL 16 (Docker) with psycopg2-binary driver
- **ORM**: SQLAlchemy 2.0.41+ (synchronous)
- **Migrations**: Alembic 1.17.1+
- **AI/LLM**: BAML 0.212.0 (type-safe LLM functions)
- **Validation**: Pydantic 2.12.3+
- **Server**: Uvicorn 0.38.0+
- **Containerization**: Docker + Docker Compose

## Architecture

### Directory Structure
```
app/
├── main.py                 # FastAPI app factory with lifespan management
├── config.py              # Pydantic Settings v2 configuration
├── database.py            # Synchronous SQLAlchemy with connection pooling
├── dependencies.py        # Dependency injection functions
├── exceptions.py          # Custom exceptions and error handlers
├── api/v1/               # API endpoints (user, settings, diet, meal)
├── models/               # SQLAlchemy models (User, WeeklyDiet, Meal, etc.)
├── schemas/              # Pydantic schemas for request/response
├── repositories/         # Data access layer (Repository pattern)
├── services/             # Business logic layer
├── auth/                 # Supabase authentication
├── middleware/           # Security, logging, rate limiting
├── utils/                # Shared utilities
└── websockets/           # WebSocket handlers

baml_src/                 # BAML LLM function definitions
├── diet.baml            # Diet generation, recipe, grocery list functions
├── clients.baml         # LLM client configurations (DietModel, ReceipeModel)
└── generators.baml      # Python/Pydantic code generation config

baml_client/             # Auto-generated BAML Python client (DO NOT EDIT)
alembic/                 # Database migrations
```

### Data Flow Pattern
1. **Route** (api/v1/*.py) → receives request, validates with Pydantic schemas
2. **Repository** (repositories/*.py) → handles database operations
3. **Service** (services/*.py) → orchestrates business logic, calls BAML functions
4. **BAML Functions** → type-safe LLM calls for diet generation, recipes, grocery lists

### Database Architecture
- **Connection Management**: Synchronous engine with psycopg2 driver
- **Pooling**: QueuePool for local PostgreSQL with standard connection pooling
- **Session Pattern**: Context manager via `get_db()` dependency
- **ID Strategy**: String IDs (not UUID objects) to prevent type mismatch errors
- **Models**: User → WeeklyDiet → Meals → MealIngredients, GroceryList
- **Docker**: PostgreSQL 16 running in Docker container with persistent volumes

## Commands

### Docker Development
```bash
# Start all services (PostgreSQL + FastAPI)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Access database directly
docker-compose exec db psql -U diet_user -d diet_db
```

### Local Development (without Docker)
```bash
# Start PostgreSQL via Docker only
docker-compose up -d db

# Start dev server locally (from api_diet/)
uvicorn app.main:app --reload --port 8000

# Run specific module
python -m app.main

# Install dependencies
pip install -r requirements.txt
```

### Database Migrations
```bash
# Apply migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### BAML
```bash
# Regenerate BAML client after editing .baml files
# (auto-generates baml_client/ directory)
# VSCode extension handles this automatically
```

### Testing
```bash
pytest                          # Run all tests
pytest tests/test_file.py      # Run specific test file
pytest -v                       # Verbose output
pytest -k "test_name"          # Run specific test
```

## Configuration

### Environment Variables
- Uses `.env` file in api_diet/ directory (copy from `.env.example`)
- Loaded via Pydantic Settings v2 (`app.config.Settings`)
- Key variables:
  - `DATABASE_URL`: PostgreSQL connection string (local: `postgresql://diet_user:diet_password_local_dev_only@localhost:5432/diet_db`)
  - `MY_OPENAI_KEY`: OpenAI API key for BAML functions
  - `DEBUG`, `ENVIRONMENT`: Application mode
  - `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`: Connection pool settings
  - `JWT_SECRET_KEY`: Secret key for JWT token generation (local development only, no complex auth)

### Authentication
- **Local Development**: No authentication required (open API)
- Default users initialized in database via `init_db.sql`
- Simple user identification without authentication complexity

## Code Patterns

### BAML Usage
```python
from baml_client import b  # Generated client

# Type-safe LLM function call
result = b.GeneraDietaSettimanale(
    dataInizio="2025-01-01",
    peso=70.0,
    altezza=175.0,
    obiettivo="lose weight",
    altri_dati="vegetarian"
)
# Returns DietaSettimanale with full type safety
```

### Database Session
```python
from app.dependencies import get_db

def endpoint(db: Session = Depends(get_db)):
    # Session automatically managed
    user = db.query(User).filter(User.id == "123").first()
```

### Repository Pattern
```python
class DietRepository(BaseRepository[WeeklyDiet]):
    def get_by_user_id(self, user_id: str) -> List[WeeklyDiet]:
        return self.db.query(WeeklyDiet).filter(
            WeeklyDiet.user_id == user_id
        ).all()
```

### Error Handling
- Custom exceptions in `app.exceptions.py`
- Global exception handlers registered in `main.py`
- HTTP exceptions for API errors
- Database connection error recovery

## Critical Rules

### IDs and Types
- **CRITICAL**: Use `String` type for IDs, NOT `UUID`
- When inserting: pass string IDs (e.g., `str(uuid.uuid4())`)
- When querying: use string comparisons
- **Rationale**: Prevents UUID type mismatch errors with Supabase

### BAML Files
- Edit only files in `baml_src/`
- Never manually edit `baml_client/` (auto-generated)
- After editing `.baml` files, regenerate client (VSCode extension handles this)
- Use Jinja2 templating in prompt strings: `{{ variable }}`

### Database Migrations
- Never edit migration files manually after creation
- Always use `alembic revision --autogenerate`
- Review auto-generated migrations before applying
- Test migrations with `alembic upgrade head` before committing

### Connection Pooling
- Development and production use QueuePool with standard settings
- Pool size: 5, Max overflow: 10 (configurable via env vars)
- Connection recycling and pre-ping enabled for stability
- Standard PostgreSQL connection on port 5432

### Dependencies
- Do NOT add dependencies without updating `requirements.txt`
- Keep versions pinned with `>=` for security updates
- Primary driver: `psycopg2-binary` (PostgreSQL compatibility)

### Docker
- All services defined in `docker-compose.yml`
- PostgreSQL data persisted in Docker volume `postgres_data`
- Database initialized with default users via `init_db.sql`
- Automatic health checks for database and API containers

## API Structure

### Endpoints
- `/api/v1/users/*` - User management
- `/api/v1/settings/*` - User settings (weight, height, goals)
- `/api/v1/diets/*` - Weekly diet plans
- `/api/v1/meals/*` - Individual meals

### Authentication
- **No authentication required** - Open API for local development
- All endpoints publicly accessible
- Default users available in database (see `init_db.sql`)
- User context passed via request params or body (no token validation)

### Response Format
- Success: 200/201 with data
- Validation errors: 422 with Pydantic error details
- Business logic errors: 400/404 with custom error messages
- Server errors: 500 with generic message (details in logs)

## Common Tasks

### Adding a New Endpoint
1. Define Pydantic schema in `app/schemas/`
2. Create repository method in `app/repositories/`
3. Implement service logic in `app/services/`
4. Add route in `app/api/v1/` and register in `router.py`

### Adding a New BAML Function
1. Define classes and function in `baml_src/*.baml`
2. Save file (VSCode extension regenerates `baml_client/`)
3. Import and use: `from baml_client import b; result = b.FunctionName(...)`

### Modifying Database Schema
1. Edit SQLAlchemy models in `app/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration file
4. Apply: `alembic upgrade head`

## Monitoring & Debugging

### Logs
- Configured in `app.main.py` via `logging.basicConfig()`
- Level controlled by `LOG_LEVEL` env var (default: INFO)
- Format: text (dev) or JSON (production)

### Metrics
- Prometheus metrics available when `ENABLE_METRICS=true`
- Endpoint: `/metrics`

### Documentation
- Swagger UI: `/docs` (protected with basic auth in production)
- ReDoc: `/redoc`
- OpenAPI spec: `/openapi.json`

## Security

### Never Commit
- `.env` file (already in .gitignore)
- Database credentials
- API keys (OPENAI, Supabase secrets)
- Generated `baml_client/` can be committed (deterministic output)

### Middleware Stack
1. SecurityHeadersMiddleware - adds security headers
2. LoggingMiddleware - request/response logging
3. RateLimitingMiddleware - rate limit protection
4. CORSMiddleware - CORS handling

## Project Migration Status

### Recent Changes
- **Removed Supabase**: Migrated from Supabase to local PostgreSQL in Docker
- **Simplified Auth**: Removed complex authentication (open API for local development)
- **Dockerized**: Full Docker Compose setup with PostgreSQL and FastAPI services
- **Default Users**: Database initialized with default test users

## Known Issues & Workarounds

### UUID Type Mismatch
- **Issue**: `psycopg2.errors.DatatypesMismatch: UUID objects are not supported`
- **Solution**: Use String type for IDs, convert UUID to string before insertion
- **Fixed in**: commit 5f7635c
