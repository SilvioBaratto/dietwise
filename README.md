# DietLogo AI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Angular 20](https://img.shields.io/badge/Angular-20-red.svg)](https://angular.dev/)

AI-powered personalized weekly meal plan generator for the Italian market. Users set their goals (weight, height, dietary preferences) and the AI generates a complete weekly diet with recipes and grocery lists.

## Architecture

```
Browser ──► Vercel (Angular SPA)
               │
               │  /api/* rewrite
               ▼
            Fly.io (FastAPI)
               │
         ┌─────┴─────┐
         ▼           ▼
    Supabase     BAML/OpenAI
    PostgreSQL   (diet generation)
```

## Tech Stack

| Layer    | Technology                         | Hosting   |
|----------|------------------------------------|-----------|
| Frontend | Angular 20, Tailwind CSS 4         | Vercel    |
| Backend  | FastAPI, SQLAlchemy, BAML          | Fly.io    |
| Database | PostgreSQL                         | Supabase  |
| Auth     | Supabase OAuth (Google, PKCE flow) | Supabase  |
| AI/LLM   | BAML + OpenAI                     | OpenAI    |

## Project Structure

```
dietwise/
├── api/                  # Backend (FastAPI)
│   ├── app/              #   Application code
│   ├── alembic/          #   Database migrations
│   ├── baml_src/         #   BAML LLM function definitions
│   ├── baml_client/      #   Auto-generated BAML client (do not edit)
│   └── docker/           #   Dockerfile
├── frontend/             # Frontend (Angular 20)
│   └── src/
├── .github/              # CI/CD workflows & templates
├── .env.example          # Environment variable reference
├── CLAUDE.md             # AI assistant guidance
└── law_diet.md           # Italian regulatory context
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- [BAML VSCode extension](https://marketplace.visualstudio.com/items?itemName=Boundary.baml-extension) (for editing `.baml` files)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/SilvioBaratto/dietwise.git
   cd dietwise
   ```

2. Create environment files:
   ```bash
   cp .env.example .env.dev
   # Edit .env.dev with your real Supabase, OpenAI, and Redis credentials
   ```

3. Start the backend:
   ```bash
   cd api
   pip install -e ".[dev]"
   alembic upgrade head
   uvicorn app.main:app --reload --port 8000
   ```

4. Start the frontend:
   ```bash
   cd frontend
   npm install
   ng serve
   ```

5. Open [http://localhost:4200](http://localhost:4200)

## Deployment

- **Backend**: `cd api && fly deploy --app api-diet`
- **Frontend**: Automatic via Vercel git integration on push to `main`

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and PR guidelines.

## License

[MIT](LICENSE)
