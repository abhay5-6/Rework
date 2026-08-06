# Rework — Multi-Tenant Cognitive Collaboration Platform

[![CI Pipeline](https://github.com/abhay5-6/collaborative-chat-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/abhay5-6/collaborative-chat-platform/actions)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-green.svg)](https://www.python.org/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)

**Rework** is a modern, enterprise-grade multi-tenant collaboration platform with channel-based workspaces, automatic AI memory indexing, WebSockets real-time sync, HttpOnly transport security, offline resiliency, and WebRTC video calling.

Built with **FastAPI**, **Next.js (App Router)**, **PostgreSQL (pgvector)**, **Zustand**, and **Vanilla CSS / Tailwind**.

---

## 📸 Key Features

- **🏢 Multi-Tenant Isolation**: Hierarchical organizational hierarchy (`Org -> Workspaces -> Channels`). Strict tenant boundaries prevent cross-tenant data leakage.
- **🔒 HttpOnly CSRF Auth Transport**: Dual-submit CSRF cookie protection + short-lived 60-second WebSocket authentication tickets. Zero long-lived bearer tokens stored in `localStorage`.
- **⚡ Real-Time Resilient Socket Engine**: Sub-10ms real-time chat, typing indicators, and presence tracking with automatic offline message queue flushing.
- **🧠 Decoupled AI Memory Indexing**: SentenceTransformers vector embeddings and Google Gemini memory extraction running asynchronously through background workers with test-mode stubs and 503 fallback banners.
- **🛡️ Quality Gate & Observability**: Complete CI pipeline release gate with Alembic database migration validation, structured JSON logging, security log sanitization, and `/health` metrics.

---

## 🏗️ System Architecture

```text
+-------------------------------------------------------------+
|                     Next.js 16 Frontend                     |
|         (Zustand Stores, Offline Queue, WebSockets)         |
+---------------------+-----------------------+---------------+
                      |                       |
            REST APIs | HttpOnly Cookies      | WS Ticket Authentication
                      v                       v
+---------------------+-----------------------+---------------+
|                    FastAPI Backend Engine                   |
|       (Centralized Auth, Rate Limiting, Route Guard)        |
+---------------------+-----------------------+---------------+
                      |                       |
            SQLAlchemy| pgvector              | ARQ Redis Jobs
                      v                       v
+---------------------+-------+   +-----------+---------------+
| PostgreSQL + pgvector DB    |   | ARQ Background Worker     |
| (Orgs, Workspaces, Channels)|   | (AI Memory & Embeddings)  |
+-----------------------------+   +---------------------------+
```

---

## 🛠️ Environment Configuration Reference

| Environment Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://rework_user:rework_password@localhost:5432/rework_db` |
| `JWT_SECRET` | Secret key for signing JWT tokens | `super-secret-jwt-key-replace-in-production!` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | HttpOnly auth token expiration | `60` |
| `FRONTEND_URL` | Origin URL of Next.js frontend | `http://localhost:3000` |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins for REST API | `http://localhost:3000` |
| `WEBSOCKET_ALLOWED_ORIGINS` | Allowed origins for WebSockets | `http://localhost:3000` |
| `AI_ENABLED` | Toggle AI features across backend | `true` |
| `AI_TEST_MODE` | Enable instant mock AI stubs | `true` (for local tests & CI) |
| `GEMINI_API_KEY` | Google Gemini AI API Key | *(Optional in dev/test)* |

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (with `pgvector` extension)
- Redis 7+

### 2. Backend Setup

```bash
cd backend

# Create & activate virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx slowapi psutil

# Configure environment variables
cp .env.example .env

# Run database migrations to current head
alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```
FastAPI REST API & Docs will be available at **`http://localhost:8000/docs`**.

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm ci

# Configure environment variables
cp .env.local.example .env.local

# Run Next.js development server
npm run dev
```
Next.js web client will be available at **`http://localhost:3000`**.

---

## 🧪 Testing & Verification Commands

### Run Backend Integration Test Suite (33 Tests)
```bash
cd backend
test_env/bin/pytest tests/ -v
```

### Run Frontend Typecheck & Linting
```bash
cd frontend
npm run type-check   # Runs tsc --noEmit
npm run lint         # Runs eslint app components lib hooks
npm run build        # Verifies Next.js production bundle build
```

---

## 📖 Operational Documentation

- **[CONTRIBUTING.md](./CONTRIBUTING.md)**: First-time contributor guide, setup workflow, and PR checklist.
- **[RUNBOOKS.md](./RUNBOOKS.md)**: Incident response runbooks (deployments, rollbacks, connection pool exhaustion, Redis outage, token revocation).
- **[SECURITY.md](./SECURITY.md)**: Security vulnerability reporting policy and disclosure process.
- **[CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)**: Community rules and standards.

---

## 📜 License

Rework is open-source software licensed under the **Apache 2.0 License**. See [LICENSE](LICENSE) for details.
