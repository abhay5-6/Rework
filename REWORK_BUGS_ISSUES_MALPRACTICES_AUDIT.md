# Rework Bugs, Issues, and Malpractices Audit

Date: 2026-07-26

Scope: read-only audit of `C:\Users\abhay\Desktop\Rework - Copy`. No application code was fixed in this pass.

## Validation Summary

- Repository identity was verified with `Get-Location` and `git rev-parse --show-toplevel`.
- Backend compile check passed: `python -m compileall app`.
- Frontend lint failed: `npm.cmd run lint` reported 8 errors and 10 warnings.
- Frontend production build failed: `npm.cmd run build` failed TypeScript checking at `frontend/app/rooms/[id]/components/ChatArea.tsx:253`.
- The worktree was already heavily modified before this audit. Treat existing modified and untracked files as user-owned.

## Critical Findings

### 1. Frontend production build is broken

Evidence:
- `npm.cmd run build` fails at `frontend/app/rooms/[id]/components/ChatArea.tsx:253`.
- `msg.is_pending` is read in `ChatArea.tsx`, but `Message` in `frontend/lib/store/roomStore.ts:4-14` has no `is_pending`, `temp_id`, or `retry_count` fields.

Impact:
- The app cannot ship a production build.
- Other TypeScript errors may still be hidden because Next stopped at the first type-check failure.

Fix direction:
- Add a typed pending-message variant, extend `Message` intentionally, or keep pending queue rendering separate from persisted server messages.

### 2. Frontend lint is broken

Evidence from `npm.cmd run lint`:
- `frontend/app/orgs/page.tsx:112` has an unescaped apostrophe.
- `frontend/app/rooms/[id]/components/RoomHeader.tsx:48` uses explicit `any`.
- `frontend/app/rooms/[id]/components/RoomRightSidebar.tsx:22`, `:27`, `:30`, and `:31` use explicit `any`.
- `frontend/app/rooms/page.tsx:82` triggers `react-hooks/set-state-in-effect`.
- There are additional unused import and hook dependency warnings in org, room, and navbar files.

Impact:
- CI or deployment pipelines that run lint will fail.
- The warning set points to unstable React effect dependencies and drifting component contracts.

Fix direction:
- Replace `any` with shared API/domain types, escape user-visible text, and revisit the affected effects.

### 3. File upload frontend is non-functional

Evidence:
- `frontend/lib/api/files.ts:12` posts `formData`, but no `FormData` object is created in the function.
- `ChatArea.tsx:140-151` calls `uploadRoomFile`, so attachment UI flows through this broken API helper.

Impact:
- Attachment uploads fail at runtime or in later type-checking once earlier build errors are resolved.
- Users can select files and see upload UI, but the request body is undefined.

Fix direction:
- Create `const formData = new FormData(); formData.append("file", file);` before posting, and add a focused upload test.

### 4. Live message sending can duplicate messages

Evidence:
- `ChatArea.tsx:134` adds every outgoing message to the persisted queue.
- `ChatArea.tsx:160-168` sends the same message over the socket immediately.
- `frontend/app/rooms/[id]/page.tsx:142-162` flushes every queued message whenever `queue` changes while connected, sending the same `temp_id` again.

Impact:
- Connected users can create duplicate chat messages.
- Retry counts are incremented after send attempts in `page.tsx:156`, even before an acknowledgement is received.

Fix direction:
- Separate "optimistic local pending message" from "offline retry queue", or only queue when the socket is unavailable.
- Make `temp_id` idempotent on the backend if retries are supported.

### 5. REST message history drops AI messages

Evidence:
- AI responses are stored with `sender_id=None` in `backend/app/websocket/chat.py:461-464`.
- Message history uses an inner join on users: `backend/app/services/message_service.py:101-103`.

Impact:
- AI messages can appear live over websocket but disappear after refresh because messages with `sender_id=None` do not join to `users`.

Fix direction:
- Use an outer join, or store AI/system sender information in a first-class message type.

### 6. Desk/channel data is not returned by REST message history

Evidence:
- `backend/app/models/message.py` includes `desk_id`.
- `backend/app/schemas/message.py:6-16` does not include `desk_id`.
- `backend/app/services/message_service.py:118-132` builds returned messages without `desk_id`.
- `frontend/app/rooms/[id]/page.tsx:337` filters messages by `m.desk_id === activeDeskId || !m.desk_id`.

Impact:
- After refresh, server-loaded messages have no `desk_id`, so they appear in every desk/channel.
- Channel separation is unreliable.

Fix direction:
- Include `desk_id` in the message response schema and formatted messages.
- Add a `desk_id` query parameter for history reads.

### 7. REST message creation cannot actually assign a desk

Evidence:
- `backend/app/schemas/message.py:6-7` only accepts `content`.
- `backend/app/services/message_service.py:71` tries `getattr(message_data, 'desk_id', None)`, but `MessageCreate` has no such field.

Impact:
- REST-created messages cannot be scoped to desks.
- The REST and websocket message contracts diverge.

Fix direction:
- Add validated `desk_id` support to `MessageCreate`, or remove the unused `getattr` path and keep all sending on one channel.

### 8. Task endpoints do not enforce room access

Evidence:
- `backend/app/routes/tasks.py:15-34` lists tasks by `room_id` for any authenticated user.
- `backend/app/routes/tasks.py:37-83` updates a room task for any authenticated user.
- Neither path calls `has_room_access` or checks `RoomMembership`.

Impact:
- Any logged-in user who can guess a room id can read and modify that room's tasks.

Fix direction:
- Apply the same room access policy used by messages/memories before listing or updating tasks.
- Consider stricter role checks for updates.

### 9. Organization-scoped rooms are not protected

Evidence:
- `backend/app/services/room_service.py:25-26` scopes duplicate-name checks by `organization_id`.
- `backend/app/services/room_service.py:38` writes `organization_id` directly from the request.
- `backend/app/routes/rooms.py:99-116` lets users list rooms by any `organization_id`.
- No organization membership check is performed in `create_room` or `get_rooms`.

Impact:
- A logged-in user can create rooms inside an organization they do not belong to.
- A logged-in user can enumerate room metadata for arbitrary organizations.

Fix direction:
- Verify `OrgMembership` before room creation and organization-filtered listing.
- Decide whether org-scoped private room metadata should be hidden from non-members.

### 10. Organization members endpoint likely returns invalid response data

Evidence:
- `backend/app/schemas/org.py:26-31` requires `org_id` in `OrgMemberSchema`.
- `backend/app/services/org_service.py:78-83` returns `user_id`, `role`, `created_at`, and `username`, but not `org_id`.

Impact:
- `GET /orgs/{org_id}/members` can raise response validation errors.
- Frontend org/member UI will be unstable once it relies on this endpoint.

Fix direction:
- Return `org_id` or remove it from the response schema.

### 11. Global unique room names conflict with org-scoped channel design

Evidence:
- `backend/app/models/room.py:26-29` sets `Room.name` as `unique=True`.
- `backend/app/services/room_service.py:23-26` tries to enforce duplicate names only within an organization.

Impact:
- Two different organizations cannot have a channel with the same name, despite the service implying they should.
- "general" or "engineering" style channels will collide globally.

Fix direction:
- Replace global uniqueness with a composite unique constraint such as `(organization_id, name)`, with a clear rule for rooms without organizations.

### 12. Alembic downgrade uses unnamed foreign-key constraints

Evidence:
- `backend/alembic/versions/01115320d056_add_organizations_and_desks.py:49` and `:51` call `op.create_foreign_key(None, ...)`.
- The downgrade at `:58` and `:60` calls `op.drop_constraint(None, ...)`.

Impact:
- Downgrades can fail because the constraint name is not known.
- Database rollback safety is weak.

Fix direction:
- Name the constraints explicitly and use the same names in downgrade.

## High-Severity Security and Reliability Issues

### 13. Docker Compose contains production-looking hardcoded secrets

Evidence:
- `docker-compose.yml:7` hardcodes `POSTGRES_PASSWORD`.
- `docker-compose.yml:23` embeds the database password in `DATABASE_URL`.
- `docker-compose.yml:24` sets `JWT_SECRET: change-me-before-deploy` while `APP_ENV` is production at `:22`.

Impact:
- Any deployment based on this compose file has predictable credentials and a predictable JWT signing key.

Fix direction:
- Move secrets to environment files or a secret manager.
- Fail startup if production uses the placeholder JWT secret.

### 14. Tokens are persisted in web storage

Evidence:
- `frontend/components/AuthProvider.tsx:59-65` stores tokens in both `sessionStorage` and `localStorage`.
- `frontend/lib/api/client.ts:13` reads from both stores.
- `frontend/lib/websocket/chat.ts:7-14` also reads from both stores.

Impact:
- XSS compromises long-lived tokens.
- Storing in both locations defeats the "sessionStorage first" safety improvement.

Fix direction:
- Prefer httpOnly, SameSite cookies or a short-lived in-memory access token with refresh-token rotation.

### 15. Websocket auth token is placed in the URL

Evidence:
- `frontend/lib/websocket/chat.ts:24-30` notes the issue and appends `?token=${token}`.

Impact:
- Tokens can leak via logs, browser history, proxies, monitoring tools, or crash reports.

Fix direction:
- Use a short-lived websocket ticket, secure cookie auth, or a websocket subprotocol approach.

### 16. OAuth state is not bound to a browser session

Evidence:
- `backend/app/routes/auth.py:134-141` creates a signed JWT state with provider, nonce, and expiration.
- `backend/app/routes/auth.py:264-270` verifies signature/expiration/provider only.
- No cookie or server-side nonce store is used to bind state to the initiating browser.

Impact:
- The state token is tamper-resistant, but it is not a full CSRF/session binding.

Fix direction:
- Store a nonce in an httpOnly SameSite cookie or server-side session and compare it during callback.

### 17. OAuth callback sends the access token in the redirect URL

Evidence:
- `backend/app/routes/auth.py:321-322` redirects to `/auth/callback?token=...`.
- `frontend/app/auth/callback/page.tsx:15-21` reads the token from the URL.

Impact:
- Tokens can leak through browser history, analytics, referrer headers, screen recordings, and support logs.

Fix direction:
- Set an httpOnly cookie from the backend callback or exchange a one-time code on the frontend.

### 18. Upload endpoint lacks size/type validation and durable storage

Evidence:
- `backend/app/routes/files.py:24` accepts arbitrary `UploadFile`.
- `backend/app/routes/files.py:40-48` writes the file directly to local `uploads`.
- `backend/app/main.py:147-148` serves the entire uploads directory statically.

Impact:
- Users can upload oversized or unsafe files.
- Files are not scanned, not quota-controlled, and not tied to durable object storage.
- Static serving relies on local disk and deployment working directory.

Fix direction:
- Enforce file size, MIME allow-list, extension checks, per-room/user quotas, and object storage.
- Consider authenticated file download routes instead of raw static serving.

### 19. Public rooms currently permit message/file access without membership

Evidence:
- `backend/app/services/message_service.py:27-30` returns access for any public room.
- `backend/app/routes/files.py:28-31` allows uploads to public rooms even when `is_member` is false and the room is not private.

Impact:
- This may be intended for discovery, but it means joining a public room is not required to read/send/upload.
- If "membership" is meant to indicate participation, permissions are too loose.

Fix direction:
- Define the intended public-room policy explicitly: discoverable only, readable, writable, or fully open.
- Enforce that policy consistently across messages, files, tasks, AI, desks, and websockets.

## Medium-Severity Product and Contract Issues

### 20. Room list leaks private room metadata

Evidence:
- `backend/app/services/room_service.py:78-89` selects rooms by organization or all rooms without filtering by membership/privacy.
- `backend/app/services/room_service.py:118-127` returns `name`, `description`, `is_private`, `owner_id`, role status, and pending-request status.

Impact:
- Authenticated users can discover private room names/descriptions they may not be allowed to access.

Fix direction:
- Decide whether private rooms should be discoverable.
- If not, filter to public rooms plus rooms where the user has membership or an approved invitation path.

### 21. Org feature has no member-management path

Evidence:
- `backend/app/routes/organization.py:6` imports `OrgMemberAdd`, but no route uses it.
- `frontend/lib/api/organizations.ts` only exposes create/list/get/members.

Impact:
- Users can create organizations but cannot invite/add/manage members through the implemented API.
- Rooms can be tied to orgs, but org collaboration is incomplete.

Fix direction:
- Add explicit member invite/add/remove/role endpoints with owner/admin enforcement.

### 22. Desk creation only checks room membership, not role

Evidence:
- `backend/app/services/desk_service.py:10-20` permits any room member to create a desk.

Impact:
- Regular members can create channels/desks, which may be fine for open collaboration but is risky if channels are meant to be admin-managed.

Fix direction:
- Decide policy and enforce it: owner/admin only, or any member.

### 23. Desk ids are not validated against room ids when sending messages

Evidence:
- `backend/app/websocket/chat.py:288-314` accepts `desk_id` from the client and passes it to `create_realtime_message`.
- `backend/app/services/message_service.py:145-161` stores `desk_id` without checking that the desk belongs to the same room.

Impact:
- A user can attach a message in one room to a desk from another room, or trigger foreign-key failures.

Fix direction:
- Validate that `Desk.id == desk_id` and `Desk.room_id == room_id` before saving.

### 24. Message ids for pending messages are hardcoded to 0

Evidence:
- `frontend/app/rooms/[id]/components/ChatArea.tsx:76` sets pending queue message `id: 0`.
- Message element ids use `id={`message-${msg.id}`}` at `ChatArea.tsx:206`.

Impact:
- Multiple pending messages share DOM ids and React keys are only rescued by index.
- This can break anchors, accessibility, and message-specific actions.

Fix direction:
- Use `temp_id` as the pending message identifier and keep server ids nullable until confirmed.

### 25. Optimistic queue stores message content in localStorage

Evidence:
- `frontend/lib/store/queueStore.ts:23-47` persists the queue with `name: "offline-queue"`.

Impact:
- Draft/offline message content remains on disk, including potentially sensitive chat/file metadata.
- There is no TTL or cleanup on logout in the audited code.

Fix direction:
- Persist only when offline support is a product requirement, encrypt or minimize stored data, and clear on logout/account switch.

### 26. WebRTC signaling trusts arbitrary payload shape

Evidence:
- `backend/app/websocket/chat.py:251` reads `inner_data = data.get("data", {})`.
- `backend/app/websocket/chat.py:260-268` rebroadcasts `**inner_data` without schema validation.

Impact:
- Clients can send malformed or oversized signaling payloads inside an otherwise acceptable websocket message.
- Future clients may crash or behave unpredictably.

Fix direction:
- Validate signaling event payloads per event type and reject unexpected keys/sizes.

### 27. Broad exception swallowing hides websocket failures

Evidence:
- `backend/app/websocket/chat.py:408-425` swallows disconnect/close errors.
- `backend/app/websocket/manager.py:67-70` and `:201-205` swallow close/send errors.

Impact:
- Connection lifecycle bugs become hard to diagnose.
- Broken broadcasts may silently drop users.

Fix direction:
- Log at debug/warning level with connection metadata, while avoiding noisy expected disconnect logs.

### 28. Debug prints remain in backend services

Evidence:
- `backend/app/websocket/chat.py:365` and `:375` use `print`.
- `backend/app/services/ai/ollama_service.py:18` and `:56` use `print`.

Impact:
- Logs are unstructured and harder to filter.
- Sensitive queries may be printed directly.

Fix direction:
- Replace with structured logger calls and avoid logging raw prompt/query content unless explicitly safe.

### 29. AI clients and embedding model are initialized at import time

Evidence:
- `backend/app/services/ai/ai_client.py:14-16` creates a Gemini client on import.
- `backend/app/services/ai/memory_extractor.py:13-15`, `memory_summary_service.py:23-25`, and `relationship_extractor.py:13-15` do the same.
- `backend/app/services/ai/embedding_service.py:10-12` loads `SentenceTransformer` at import time.

Impact:
- App startup can become slow or fail due to optional AI dependencies/config.
- Testing unrelated routes becomes heavier than necessary.

Fix direction:
- Lazy-load AI clients/models and surface clear feature-disabled errors when keys/models are missing.

### 30. Development `create_all` can mask migration problems

Evidence:
- `backend/app/main.py:45-49` runs `Base.metadata.create_all` whenever `APP_ENV == "development"`.

Impact:
- Local databases can drift from Alembic migrations.
- Migration bugs may be hidden during development and discovered only later.

Fix direction:
- Prefer Alembic migrations even in development, or make `create_all` an explicit one-off bootstrap command.

### 31. `/db-test` exposes database error details

Evidence:
- `backend/app/main.py:162-174` returns raw exception text from database connection failures.

Impact:
- In exposed environments, this can leak infrastructure details.

Fix direction:
- Restrict to development or return generic errors while logging details server-side.

### 32. API client has no default base URL fallback

Evidence:
- `frontend/lib/api/client.ts:5-7` sets `baseURL` directly from `process.env.NEXT_PUBLIC_API_URL`.

Impact:
- Misconfigured local/dev environments silently produce relative API requests to the Next server instead of the backend.

Fix direction:
- Provide an explicit development fallback or fail loudly in app startup.

### 33. User-facing login/register copy says OAuth is coming soon while backend OAuth exists

Evidence:
- `frontend/app/login/page.tsx:108` says Google and GitHub sign-in are "next up".
- Backend has `/auth/providers`, `/auth/{provider}/start`, and callback routes in `backend/app/routes/auth.py`.

Impact:
- Product state is inconsistent.
- Users cannot discover configured OAuth providers from the login UI.

Fix direction:
- Wire frontend provider buttons to `/auth/providers` and `/auth/{provider}/start`, or hide backend OAuth until ready.

## Lower-Severity Maintainability Issues

### 34. Several files contain unused imports and dead variables

Evidence:
- `frontend/app/orgs/page.tsx:9` imports `Organization` unused.
- `frontend/app/orgs/page.tsx:42` assigns `newOrg` unused.
- `frontend/components/Navbar.tsx:9` imports unused org types.
- `frontend/app/rooms/[id]/components/RoomHeader.tsx:2` imports unused icons.

Impact:
- Small but steady codebase entropy.
- It makes real dependency changes harder to review.

Fix direction:
- Remove unused imports/variables as part of lint cleanup.

### 35. There are inconsistent storage lookup orders

Evidence:
- `frontend/lib/api/client.ts:13` uses `sessionStorage || localStorage`.
- `frontend/lib/websocket/chat.ts:7-14` uses the same order.
- `frontend/app/rooms/[id]/page.tsx:202` uses `localStorage || sessionStorage`.

Impact:
- If both stores contain different tokens, API and websocket code may authenticate as different sessions.

Fix direction:
- Use one canonical token source, or remove dual storage entirely.

### 36. Pagination count loads all rooms into memory

Evidence:
- `backend/app/services/room_service.py:78-82` selects rooms and calculates `len(result.scalars().all())`.

Impact:
- Room listing grows inefficiently with data volume.

Fix direction:
- Use `select(func.count())` with the same filters.

### 37. Room delete manually deletes related rows

Evidence:
- `backend/app/services/room_service.py:284-310` fetches and deletes memberships/messages manually before deleting the room.

Impact:
- Easy to miss related tables as the model grows.
- More queries and more failure points.

Fix direction:
- Use database cascades deliberately and test deletion behavior.

### 38. Error handling is inconsistent across frontend API helpers

Evidence:
- `frontend/lib/api/rooms.ts:4-33` catches and returns `[]`.
- Most other API helpers throw errors to callers.

Impact:
- Some failures are silent, making UI states misleading.

Fix direction:
- Standardize API helpers: either throw and let pages handle UX, or return typed result objects.

### 39. Generated migration comment remains unreviewed

Evidence:
- `backend/alembic/versions/01115320d056_add_organizations_and_desks.py:22` says the commands were auto-generated and should be adjusted.

Impact:
- This aligns with the unnamed-constraint downgrade issue and suggests the migration has not been production-reviewed.

Fix direction:
- Review generated migrations before commit, name constraints, and add downgrade verification.

### 40. No tests were found in the audited file list

Evidence:
- `rg --files` did not show frontend or backend test files.

Impact:
- Current breakages reached the worktree without automated coverage catching them.
- Critical paths like auth, room permissions, desk scoping, websocket message acknowledgements, upload, and migrations are unguarded.

Fix direction:
- Add focused backend tests for access control and API contracts.
- Add frontend unit/component tests for queue/send behavior and API helpers.
- Add at least one build/lint CI gate.

## Suggested Fix Priority

1. Restore frontend build and lint: `is_pending`, `formData`, explicit `any`, unescaped text, hook errors.
2. Fix access control: tasks, org-scoped rooms, private room metadata, desk ownership validation.
3. Repair message/desk contracts: `desk_id` in create/list responses, desk-filtered history, AI messages in history.
4. Rework optimistic/offline queue to avoid duplicates and localStorage leakage.
5. Harden auth/OAuth/token handling and websocket authentication.
6. Harden uploads: validation, quotas, authenticated serving, durable storage.
7. Clean migration/deploy hygiene: named constraints, no hardcoded production secrets, avoid `create_all` drift.
8. Add test coverage and CI gates before adding more product surface.

## Commands Run

```powershell
Get-Location
git rev-parse --show-toplevel
git status --short
rg --files
git diff --stat
npm.cmd run lint
npm.cmd run build
python -m compileall app
rg -n "...targeted patterns..." frontend backend docker-compose.yml README.md plan.md
```

