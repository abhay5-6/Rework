# Contributing to Rework

Thank you for your interest in contributing to **Rework**! We welcome contributions from developers of all skill levels, including students, open-source first-timers, and experienced engineers.

This guide outlines our development setup, testing standards, code style, and pull request workflow.

---

## 🧭 Contributor Path (First-Time Contributor Quickstart)

If you are a new contributor, follow these steps to make your first contribution without needing private help:

### 1. Fork & Clone Repository
```bash
git clone https://github.com/YOUR-USERNAME/collaborative-chat-platform.git
cd collaborative-chat-platform
```

### 2. Configure Local Non-Secret Defaults
Copy the provided environment example files which contain working non-secret local defaults:
```bash
# Backend configuration
cp backend/.env.example backend/.env

# Frontend configuration
cp frontend/.env.local.example frontend/.env.local
```

### 3. Setup & Run Database Migrations
```bash
cd backend
python -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx slowapi psutil

alembic upgrade head
```

### 4. Run Automated Test Suite
Make sure all backend tests pass locally before editing any code:
```bash
test_env/bin/pytest tests/ -v
```

### 5. Frontend Development & Typecheck
```bash
cd ../frontend
npm ci
npm run type-check
npm run lint
```

---

## 🏷️ Good First Issue Tasks

Looking for an issue to start with? Look for issues tagged with `good first issue` on GitHub.

Good first issue tasks always include:
1. **Clear reproduction steps** or target file locations.
2. **Explicit acceptance criteria**.
3. **Automated test instructions**.

Example candidate tasks:
- Adding a new UI icon or tooltip to workspace settings.
- Adding a test case for specific error HTTP status codes.
- Cleaning up unused imports or TypeScript type annotations.

---

## 📜 Pull Request Guidelines

Before submitting a Pull Request (PR), please verify:

1. **Clean Commit History**: Write clear, conventional commit messages (`feat: ...`, `fix: ...`, `test: ...`, `docs: ...`).
2. **Zero Linting & Type Errors**:
   ```bash
   cd frontend
   npm run type-check
   npm run lint
   ```
3. **Passing Test Suite**:
   ```bash
   cd backend
   test_env/bin/pytest tests/ -v
   ```
4. **No Committed Secrets**: Never commit `.env` files, API keys, JWT secrets, passwords, or production credentials.

---

## 🔒 Security & Code Standards

- **Backend**: Always use `logger = logging.getLogger(__name__)` with `extra={...}` context. Do not use raw `print()` statements.
- **Frontend**: Log errors gracefully or use toast notifications (`toast.error()`). Do not swallow errors silently in try/catch blocks.
- **API Security**: Maintain strict type hints (`str`, `int`, `list`, `dict`), use `Depends()` for database sessions, and enforce tenant permission checks on all protected endpoints.

---

## 💬 Getting Help

If you run into documentation gaps or setup issues, please open an Issue on GitHub describing the step where you got stuck so we can improve our documentation!
