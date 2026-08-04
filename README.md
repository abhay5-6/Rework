# Rework - Cognitive Workspace & Real-Time Collaboration Platform

A modern, open-source, multi-tenant collaboration platform with channel-based workspaces, automatic AI memory indexing, WebSockets, offline resiliency, and WebRTC video calls.

Built with **FastAPI**, **Next.js (App Router)**, **PostgreSQL**, **Zustand**, and **TailwindCSS**.

---

## ✨ Features & Highlights

### 🏢 Multi-Tenant Organizations & Workspaces
- **Organizations**: Root tenant context (`Org -> Workspaces -> Channels`).
- **Workspaces (Rooms)**: Public or private workspaces within an organization.
- **Channels (Desks)**: Topic-based communication channels (e.g., `#general`, `#dev`).
- **Governance**: Granular owner, admin, and member role-based access control.

### ⚡ Real-Time Messaging & Resilient Engine
- **WebSocket Engine**: Sub-10ms real-time chat, typing indicators, and online presence tracking.
- **Offline Queue**: Messages typed while offline are stored securely in `localStorage` (`queueStore`) and automatically flushed upon WebSocket reconnection.
- **Optimistic UI**: Instant visual message rendering with sending/retry state badges.

### 🧠 Automatic AI Memory Indexing
- **Semantic Extraction**: Asynchronously extracts decisions, notes, and tasks from messages into room memory.
- **AI Assistant & Knowledge Graph**: Query room memory directly in the AI Assistant panel or visualize connections in the Interactive Memory Graph.

### 📹 Live Video Calls & Task Board
- **WebRTC Mesh Video**: Peer-to-peer audio/video calling within any workspace channel.
- **Kanban Board**: Drag-and-drop task management built into every workspace.

---

## 🏗️ System Architecture

For a deep dive into the database domain model, real-time message flow, and AI extraction engine, read our [ARCHITECTURE.md](./ARCHITECTURE.md).

```
+-------------------------------------------------------------+
|                     Next.js 14 Frontend                     |
|         (Zustand Stores, Offline Queue, React Hooks)         |
+---------------------+-----------------------+---------------+
                      |                       |
            REST APIs |                       | WebSockets
                      v                       v
+---------------------+-----------------------+---------------+
|                    FastAPI Backend Engine                   |
|         (Authentication, Room Logic, Socket Manager)        |
+---------------------+-----------------------+---------------+
                      |                       |
            SQLAlchemy|                       | Async Tasks
                      v                       v
+---------------------+-------+   +-----------+---------------+
| PostgreSQL Database         |   | AI Memory Extractor       |
| (Orgs, Rooms, Desks, Chat)  |   | (SentenceTransformers / Vector)|
+-----------------------------+   +---------------------------+
```

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 14 (App Router) + React 18
- **State Management**: Zustand (with LocalStorage Persistence)
- **Styling**: Vanilla TailwindCSS + Lucide Icons + Next-Themes (Dark/Light mode)
- **Real-Time & Calls**: Custom WebSocket Engine + WebRTC

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + SQLAlchemy (Async ORM) + AsyncPG
- **Security**: JWT Authentication + Password Hashing (Bcrypt) + Rate Limiting
- **AI & ML**: Gemini / Ollama + SentenceTransformers (Vector Embeddings)

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL database instance

### 2. Backend Setup

```bash
cd backend

# Create & activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Apply database migrations
alembic upgrade head

# Seed the development database (optional)
python scripts/seed_dev.py

# Run FastAPI development server
uvicorn app.main:app --reload
```

The backend server will run on **`http://127.0.0.1:8000`**.

### 3. Frontend Setup

```bash
cd frontend

# Install npm dependencies
npm install

# Configure environment variables
cp .env.example .env.local

# Run Next.js development server
npm run dev
```

The frontend application will run on **`http://localhost:3000`**.

---

## 📜 License & Contribution

Rework is open-source software licensed under the **Apache 2.0 License**.

Contributions are welcome! Please check our [ARCHITECTURE.md](./ARCHITECTURE.md) to understand the system design before submitting Pull Requests.

Built with ❤️ by Abhay Tewatia and the open-source community.
