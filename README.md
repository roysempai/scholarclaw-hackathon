# ScholarClaw

AI-powered Scholarship Agent for Indian Students

## Overview

ScholarClaw helps Indian students discover, qualify for, and apply to government and private scholarship schemes using AI agents powered by Anthropic's Claude.

## Tech Stack

- **Backend**: FastAPI (Python 3.11) + Prisma ORM + PostgreSQL
- **Frontend**: React 18 + Vite + TailwindCSS
- **AI**: LangGraph + Anthropic Claude API
- **Security**: ArmorIQ integration + Pytector prompt injection detection

## Project Structure

```
scholarclaw/
├── backend/          # FastAPI application
├── frontend/         # React + Vite application
├── tasks/            # Task definitions for each module
└── vendor/           # Third-party libraries (fastapi-rbac, pytector)
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker (optional)

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
prisma generate
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Docker Setup

```bash
docker-compose up -d
```

## Environment Variables

Copy `.env.example` to `.env` and fill in the required values.

## License

Private - All rights reserved
