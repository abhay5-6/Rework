# Rework Agent Rules

These rules apply to all AI agents working within this workspace. You MUST follow them strictly.

## 1. Documentation Requirements
- When modifying or creating Python services, routes, repositories, or models, you must provide comprehensive Python docstrings (explaining arguments, return types, and exceptions raised).
- When modifying or creating React hooks, Zustand stores, or API clients, you must include JSDoc comments.

## 2. Logging Requirements
- Do not use `print()` statements for backend logic. Always use `logger = logging.getLogger(__name__)`.
- When logging, use the `extra` kwarg to provide context (e.g., `logger.info("Created memory", extra={"room_id": room_id, "user_id": user_id})`).
- For the frontend, do not swallow errors in try/catch blocks silently. Log errors gracefully or use the UI toast notification system (`toast.error()`).

## 3. Artifacts and File Hygiene
- Do not commit artifacts, temporary scratch files, or planning markdown files to the repository. Local planning Markdown files are allowed, but must remain ignored and uncommitted. The `.gitignore` prevents `*.md` from being tracked, EXCEPT `README.md` and `CONTRIBUTING.md`. Do not bypass this rule.
- Do not create scratch files or artifact files directly in the repository root if they are meant for agent planning. Store them in the agent's dedicated `.gemini/` artifact directory.

## 4. Architecture and Design
- Always use `Depends` in FastAPI routes for database connections and user sessions.
- Maintain the separation of concerns: Business logic in `services/`, database queries in `repositories/`, and HTTP responses in `routes/`.
- Ensure strict type-hinting in Python (`str`, `int`, `list`, `dict`) and TypeScript. Avoid `Any` wherever possible.
