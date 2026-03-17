# DietLogo AI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Angular 21](https://img.shields.io/badge/Angular-21-red.svg)](https://angular.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688.svg)](https://fastapi.tiangolo.com/)
[![Deployed on Vercel](https://img.shields.io/badge/Vercel-deployed-black.svg)](https://diet.silviobaratto.com)
[![Deployed on Fly.io](https://img.shields.io/badge/Fly.io-deployed-7b36ed.svg)](https://api-diet.fly.dev)

AI-powered personalized weekly meal plan generator for the Italian market. Users set their goals (weight, height, dietary preferences) and the AI generates a complete weekly diet with recipes and grocery lists.

> **Regulatory note** — This application is positioned as a general wellness and informational tool, not a medical device. It complies with the Italian and EU regulatory framework for nutrition apps. See [`law_diet.md`](law_diet.md) for the full legal analysis covering MDR classification, GDPR health-data obligations, consumer protection, and AI Act transparency requirements.

## Demo

![DietLogo AI Demo](video.gif)

## Architecture

```
Browser ──► Vercel CDN (Angular SPA)
               │
               │  /api/* rewrite
               ▼
           Fly.io (FastAPI, Frankfurt region)
               │
         ┌─────┴──────┐
         ▼            ▼
    Supabase      BAML → LLM
    PostgreSQL    (diet generation)
```

The frontend is a single-page Angular application hosted on Vercel. All `/api/*` requests are rewritten at the edge to the FastAPI backend running on Fly.io. Authentication uses Supabase OAuth (Google sign-in with PKCE flow), with JWTs validated server-side on every request. Diet plans are generated via type-safe LLM calls through [BAML](https://docs.boundaryml.com/).

### Key design decisions

- **BYOK (Bring Your Own Key)** — Users provide their own LLM API key, encrypted at rest with AES-256-GCM. The platform never stores plaintext keys.
- **Type-safe AI** — BAML defines strongly typed function signatures for the LLM, ensuring structured Italian-language output (7 days, 5 meals each, with macros and ingredients).
- **Repository pattern** — Backend follows Route → Service → Repository → SQLAlchemy Models, keeping business logic decoupled from data access.
- **Standalone components** — Frontend uses Angular 21 standalone components with signals, OnPush change detection, and lazy-loaded routes.

## Tech Stack

| Layer | Technology | Hosting |
|-------|-----------|---------|
| Frontend | Angular 21, Tailwind CSS 4, RxJS | Vercel |
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic v2 | Fly.io |
| Database | PostgreSQL 16 | Supabase |
| Auth | Supabase OAuth (Google, PKCE flow) | Supabase |
| AI/LLM | BAML + OpenAI (user BYOK) | OpenAI |
| Encryption | AES-256-GCM (API key encryption) | Server-side |
| CI/CD | GitHub Actions | GitHub |

## Project Structure

```
dietwise/
├── api/                          # Backend (FastAPI)
│   ├── app/
│   │   ├── main.py               # Application entry point
│   │   ├── config.py             # Pydantic Settings configuration
│   │   ├── database.py           # SQLAlchemy engine & sessions
│   │   ├── api/v1/               # Versioned API routes
│   │   ├── auth/                 # Supabase JWT validation
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── repositories/         # Data access layer
│   │   ├── services/             # Business logic & BAML orchestration
│   │   └── middleware/           # Security, logging, rate limiting
│   ├── baml_src/                 # BAML LLM function definitions (edit these)
│   ├── baml_client/              # Auto-generated BAML client (do not edit)
│   ├── alembic/                  # Database migrations
│   └── docker/                   # Dockerfile for production
├── frontend/                     # Frontend (Angular 21)
│   ├── src/
│   │   ├── app/
│   │   │   ├── auth/             # Login, callback, pending-approval
│   │   │   ├── components/       # Dashboard, weekly view, recipes, settings
│   │   │   ├── services/         # HTTP services (diet, meal, recipe, auth)
│   │   │   ├── models/           # TypeScript interfaces
│   │   │   ├── guard/            # Route guards
│   │   │   ├── interceptors/     # Auth interceptor (JWT, 401 handling)
│   │   │   └── shared/           # Sidebar, cost badge, error toast
│   │   └── environments/         # Dev & production configs
│   └── vercel.json               # Vercel routing & security headers
├── .github/workflows/            # CI/CD pipelines
│   ├── frontend.yml              # Build, test, deploy frontend
│   ├── deploy-backend.yml        # Deploy backend to Fly.io
│   └── ci-backend.yml            # Lint & test backend
├── .env.example                  # Environment variable reference
├── law_diet.md                   # Italian/EU regulatory analysis
├── CONTRIBUTING.md               # Development guidelines
└── LICENSE                       # MIT
```

## Getting Started

### Prerequisites

- **Python 3.11+** (backend)
- **Node.js 20+** (frontend)
- **PostgreSQL** database (or a [Supabase](https://supabase.com/) project)
- **Supabase project** with Google OAuth configured
- **BAML VSCode extension** (recommended for editing `.baml` files): [Install](https://marketplace.visualstudio.com/items?itemName=Boundary.baml-extension)

### 1. Clone the repository

```bash
git clone https://github.com/SilvioBaratto/dietwise.git
cd dietwise
```

### 2. Configure environment variables

```bash
cp .env.example .env.dev
```

Open `.env.dev` and fill in the required values:

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_DB_URL` | Yes | PostgreSQL connection string from Supabase |
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase publishable (anon) key |
| `API_KEY_ENCRYPTION_SECRET` | Yes | 32-byte base64 key for AES-256-GCM encryption |
| `OPENAI_API_KEY` | No | Fallback LLM key for admin/testing (users bring their own) |
| `REDIS_URL` | No | Redis URL for caching (defaults to in-memory) |

Generate an encryption secret:

```bash
python3 -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"
```

### 3. Start the backend

```bash
cd api
pip install -e ".[dev]"
alembic upgrade head          # Apply database migrations
uvicorn app.main:app --reload --port 8000
```

The API is now available at [http://localhost:8000](http://localhost:8000). Swagger docs are at [http://localhost:8000/docs](http://localhost:8000/docs).

### 4. Start the frontend

```bash
cd frontend
npm install
ng serve
```

Open [http://localhost:4200](http://localhost:4200). The dev environment automatically proxies `/api/*` requests to `localhost:8000`.

### 5. Sign in

Click **Sign in with Google**. On first login, the backend automatically creates a user record linked to your Supabase identity.

### 6. Add your LLM key

Navigate to **Settings** and enter your OpenAI API key. The key is encrypted with AES-256-GCM before being stored in the database. You can update or rotate your key at any time.

### 7. Generate a meal plan

Go to the **Dashboard**, fill in your profile (weight, height, age, sex, goals), and click **Generate**. The AI produces a full 7-day Italian meal plan with:

- 5 meals per day (colazione, spuntino mattina, pranzo, spuntino pomeriggio, cena)
- Macronutrient breakdown per meal
- Full ingredient list with quantities
- Auto-generated grocery list

## API Reference

The backend exposes the following endpoint groups under `/api/v1`:

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/diet/generate` | Generate a new weekly diet plan |
| `GET /api/v1/diet/` | List user's generated diets |
| `GET /api/v1/diet/{id}` | Get a specific diet with all meals |
| `GET /api/v1/meals/{diet_id}` | Get meals for a diet |
| `GET /api/v1/recipes/` | List saved recipes |
| `POST /api/v1/recipes/` | Save a recipe |
| `GET /api/v1/settings/` | Get user settings |
| `PUT /api/v1/settings/` | Update user settings (weight, height, goals) |
| `POST /api/v1/api-keys/` | Store an encrypted LLM API key |
| `DELETE /api/v1/api-keys/` | Remove stored API key |

All endpoints require a valid Supabase JWT in the `Authorization: Bearer <token>` header.

Full interactive documentation is available at `/docs` (Swagger UI) when running the backend.

## Deployment

### Backend (Fly.io)

The backend runs on Fly.io in the Frankfurt (`fra`) region. Database migrations run automatically before each deployment via the `release_command` in `fly.toml`.

```bash
cd api
fly deploy --app api-diet
```

Required Fly.io secrets (set with `fly secrets set`):

- `SUPABASE_DB_URL`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `API_KEY_ENCRYPTION_SECRET`

### Frontend (Vercel)

The frontend deploys automatically to Vercel on every push to `main`. Pull requests create preview deployments with unique URLs.

Manual deploy:

```bash
cd frontend
vercel --prod
```

The `vercel.json` configuration handles:

- **API proxy** — `/api/*` rewrites to `https://api-diet.fly.dev/api/*`
- **SPA fallback** — All non-API routes serve `index.html`
- **Security headers** — CSP, X-Frame-Options, Referrer-Policy, Permissions-Policy

### CI/CD Pipelines

All workflows are **path-scoped** to avoid unnecessary builds:

| Workflow | Trigger | Steps |
|----------|---------|-------|
| `frontend.yml` | Push/PR with `frontend/**` changes | Build → Test → Deploy (preview on PR, production on merge) |
| `deploy-backend.yml` | Push to `main` with `api/**` changes | Deploy to Fly.io |
| `ci-backend.yml` | Push/PR with `api/**` changes | Lint (ruff + black) → Test (pytest) → Docker build |

Required GitHub Secrets: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `FLY_API_TOKEN`

## Regulatory Compliance

This application operates under a complex Italian and EU regulatory framework. The full legal analysis is in [`law_diet.md`](law_diet.md) and covers:

- **Medical device classification** — Excluded from MDR 2017/745 per MDCG 2019-11 Rev.1 (wellness app, not a medical device). The app must never use therapeutic language ("cura", "trattamento", "terapia") or claim to diagnose/treat conditions.
- **GDPR health data** — Weight, height, BMI, and health goals qualify as health data under Art. 9 GDPR. The app requires explicit consent with granular checkboxes, a mandatory DPIA, and likely a DPO.
- **International data transfers** — Vercel and Fly.io are certified under the EU-US Data Privacy Framework. OpenAI requires Standard Contractual Clauses (SCCs) and a Transfer Impact Assessment.
- **Italian consumer protection** — The app falls under the Codice del Consumo (D.Lgs. 206/2005). Clauses excluding liability for health damages are absolutely void.
- **EU AI Act** — Classified as limited-risk AI. Art. 50 transparency obligations apply from August 2026: users must be informed they interact with an AI system, and AI-generated content must be machine-readable marked.
- **Professional practice law** — Prescribing personalized dietary plans without qualification is a criminal offense (Cassazione Penale n. 20281/2017, Art. 348 c.p.). The app is positioned strictly as informational, never as professional dietary consultation.

The [`law_diet.md`](law_diet.md) file also contains draft templates for the medical disclaimer, terms and conditions, privacy policy, and a pre-launch compliance checklist.

## Security

- **Authentication** — Supabase OAuth with Google (PKCE flow), server-side JWT validation on every request
- **API key encryption** — User LLM keys encrypted with AES-256-GCM (BYOK model)
- **Rate limiting** — Configurable per-endpoint rate limiting (default: 100 requests/60 seconds)
- **Security headers** — CSP, X-Frame-Options: DENY, Referrer-Policy, Permissions-Policy
- **CORS** — Restricted to the frontend domain
- **Middleware stack** — SecurityHeaders → Logging → RateLimiting → CORS (order matters)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code standards, and PR guidelines.

## License

[MIT](LICENSE)
