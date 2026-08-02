# Rework System Architecture

Rework is an intelligent, multi-tenant cognitive workspace platform designed for real-time collaboration, instant communication, channel-based organization, and automatic AI memory indexing.

---

## 🏛️ High-Level Domain Model

Rework follows a hierarchical multi-tenant structure to isolate team contexts cleanly:

```
+-----------------------------------------------------------------------+
|                             ORGANIZATION                              |
|   (Root tenant: Company, Team, or Personal Organization space)        |
+-----------------------------------++----------------------------------+
                                    ||
                                    || contains
                                    \/
+-----------------------------------------------------------------------+
|                            ROOM (Workspace)                           |
|   (Shared space: e.g. "Engineering", "Product", "General Workspace")  |
+-----------------------------------++----------------------------------+
                                    ||
                                    || contains
                                    \/
+-----------------------------------------------------------------------+
|                            DESK (Channel)                             |
|   (Topic channel: e.g. "#general", "#frontend", "#announcements")     |
+-----------------------------------++----------------------------------+
                                    ||
                                    || scopes
                                    \/
+-----------------------------------------------------------------------+
|                               MESSAGE                                 |
|   (Chat content, attachments, temp_id tracking, AI responses)         |
+-----------------------------------------------------------------------+
```

### Entity Definitions & Relationships:

- **Organization**: `id`, `name`, `created_by`, `created_at`
  - Has many **OrgMemberships** (`user_id`, `org_id`, `role`)
  - Has many **Rooms** (`organization_id`)
- **Room (Workspace)**: `id`, `name`, `description`, `is_private`, `ai_enabled`, `organization_id`, `owner_id`
  - Has many **RoomMemberships** (`user_id`, `room_id`, `role`)
  - Has many **Desks** (`room_id`)
  - Has many **Messages** (`room_id`)
  - Has many **Memories** (`room_id`)
  - Has many **Tasks** (`room_id`)
- **Desk (Channel)**: `id`, `name`, `description`, `room_id`
  - Scopes **Messages** (`desk_id`)
- **Message**: `id`, `content`, `sender_id` *(null for AI)*, `room_id`, `desk_id`, `extra_data`, `created_at`

---

## 🔄 Real-Time Messaging & Offline Queue Pipeline

Messages move seamlessly between the Next.js frontend, Zustand local stores, persistent WebSockets, and PostgreSQL storage:

```
[ User Types Message & Clicks Send ]
                 |
                 v
     +-----------------------+
     | Is WebSocket Online?  |
     +-----------+-----------+
                 |
        +--------+--------+
        |                 |
     ( YES )           ( NO )
        |                 |
        v                 v
+------------------+  +---------------------------------------------+
| Send over Socket |  | Add to queueStore (Persisted in localStorage)|
|  (chat_message)  |  | Render optimistic UI with "Sending..." badge |
+--------+---------+  +----------------------+----------------------+
         |                                   |
         v                                   | (On Reconnect)
+------------------+                         v
| FastAPI Backend  |  <----------------------+ (Auto-Flush Queue)
|  Save & Broadcast|
+--------+---------+
         |
         v
+------------------+
| Update UI Store  |
| Clear temp_id    |
+------------------+
```

---

## 🤖 Automatic AI Memory Extraction Pipeline

When room AI is enabled, incoming chat messages automatically pass through the asynchronous memory indexing engine to make room decisions findable:

```
[ Incoming Chat Message ]
           |
           v
+----------------------+      NO       +-----------------------+
|  AI Enabled for Room? | ------------> | Persist Message Only  |
+----------+-----------+               +-----------------------+
           | YES
           v
+--------------------------------------+
| Spawn Background Async Processing    |
+------------------+-------------------+
                   |
                   v
+--------------------------------------+
| Memory Extractor Service             |
| (Evaluates Importance & Content)     |
+------------------+-------------------+
                   |
                   v
+--------------------------------------+
| SentenceTransformer Vector Embeddings|
+------------------+-------------------+
                   |
                   v
+--------------------------------------+
| Store in RoomMemory DB Table         |
| (Available in AI Panel & Graph)      |
+--------------------------------------+
```

---

## 📂 Project Directory Breakdown

```
Rework/
├── backend/
│   ├── app/
│   │   ├── api/          # Extra REST dependencies & helpers
│   │   ├── core/         # Security, JWT tokens, DB sessions, configuration
│   │   ├── db/           # Async SQLAlchemy engine & base model definitions
│   │   ├── models/       # Database models (User, Room, Desk, Message, Org, Memory, Task)
│   │   ├── routes/       # FastAPI route handlers (auth, rooms, desk, organization, tasks, etc.)
│   │   ├── schemas/      # Pydantic validation schemas
│   │   ├── services/     # Core business logic (room management, messaging, AI extraction)
│   │   ├── utils/        # Permission helpers & string sanitization
│   │   └── websocket/    # Real-time WebSocket connection manager & route event handlers
│   └── main.py           # FastAPI application entrypoint & middleware configuration
└── frontend/
    ├── app/              # Next.js App Router pages (/login, /rooms, /orgs, /auth/callback)
    ├── components/       # Reusable UI components (Navbar, ThemeToggle, AIAssistantPanel, KanbanBoard)
    ├── hooks/            # Custom React hooks (useWebRTC, room state selectors)
    └── lib/              # API clients, Zustand state stores (roomStore, orgStore, queueStore), auth helpers
```
