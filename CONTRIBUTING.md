# Contributing to DietLogo AI

## Prerequisites

- Python 3.11+
- Node.js 20+
- [BAML VSCode extension](https://marketplace.visualstudio.com/items?itemName=Boundary.baml-extension)

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/SilvioBaratto/dietwise.git
   cd dietwise
   ```

2. Create environment files:
   ```bash
   cp .env.example .env.dev
   # Fill in your Supabase, OpenAI, and Redis credentials
   ```

3. Install the backend:
   ```bash
   cd api
   pip install -e ".[dev]"
   alembic upgrade head
   ```

4. Install the frontend:
   ```bash
   cd frontend
   npm install
   ```

## Code Standards

### Backend (Python)

- Formatter: **black** (line length 88)
- Linter: **ruff**
- Functions: max **50 lines**
- Files: max **500 lines**
- IDs: always `String` type, never `UUID` objects (Supabase compatibility)
- Run checks: `cd api && ruff check . && black --check .`

### Frontend (TypeScript/Angular)

- Formatter: **prettier**
- Use `input()`/`output()` functions, not decorators
- Use `inject()`, not constructor DI
- Use native control flow (`@if`, `@for`), not structural directives
- Standalone components only (no NgModules), OnPush change detection

## PR Process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure linting passes (backend: `ruff check . && black --check .`, frontend: `ng build`)
4. Open a PR against `main` with a clear description

## Files Not to Modify Without Discussion

- `baml_client/` (auto-generated from `baml_src/`)
- Migration files in `alembic/versions/`
- Auth core (`api/app/auth/`)
- Build configs (`angular.json`, `fly.toml`)
- Test files (`*.spec.ts`, `test_*.py`)
