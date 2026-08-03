# Contributing to Rework

Welcome to the Rework project! To ensure our codebase remains maintainable, reliable, and welcoming to all developers, we enforce the following coding standards and guidelines.

## 1. Documentation & Comments
- **Backend (Python)**: Every service, repository, route, and model must have a descriptive docstring. Explain what the function does, its arguments, and its return values. If it raises specific domain exceptions, document those as well.
- **Frontend (TypeScript/React)**: Use JSDoc comments for all custom hooks, Zustand stores, and complex UI components. Explain the purpose of the hook/component and any non-obvious side effects.
- **In-line Comments**: Use in-line comments to explain *why* something is done, not *what* is done, especially for complex state management, AI integrations, or WebRTC signaling.

## 2. Logging & Error Handling
- **Structured Logging (Backend)**: Always use the configured Python `logging` module (`logger = logging.getLogger(__name__)`). Do not use `print()`. 
- **Context-Aware Logs**: When logging information, include relevant context (e.g., `user_id`, `room_id`, `message_id`) using the `extra` kwarg: `logger.info("Message sent", extra={"room_id": 123})`.
- **Frontend Errors**: Do not swallow errors. Avoid generic `console.error(err)`. Provide descriptive error messages and use proper error boundaries. When showing toasts to users, use user-friendly language.
- **Domain Exceptions**: The backend should raise domain-specific exceptions (e.g., `RoomNotFoundException`) rather than generic HTTP exceptions in the service layer.

## 3. Clean Code & Architecture
- **Dependency Injection**: Use FastAPI's `Depends` for all database sessions and current user state. Do not instantiate database sessions manually inside services.
- **Separation of Concerns**: Keep routes thin. Business logic belongs in the `services/` layer. Database queries belong in the `repositories/` layer.
- **Type Hinting**: All Python functions and TypeScript definitions must have strict type hints. Do not use `Any` unless absolutely necessary.
- **Clean Imports**: Remove unused imports. Group imports logically (standard library, third-party, local).

## 4. Git Workflow
- Always create a feature branch for new work (e.g., `feature/add-auth`).
- Do not commit artifacts, `.md` files that belong to AI memory, or temporary scratchpads to the repository. Only commit code, configuration, and essential project documentation (`README.md`, `CONTRIBUTING.md`).

Thank you for helping keep Rework clean and robust!
