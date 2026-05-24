# 🔐 Secure Management Platform

A Python application focused on security and private messaging.

---

## 📦 Application Overview

| App | Description | Port |
|-----|-------------|------|
| 💬 [`apps/messenger`](apps/messenger/) | Secure encrypted messaging REST API (FastAPI + SQLite) | 8000 |

---

## 💬 Messenger App

A **secured REST API** for private messaging built with **FastAPI**.  
Messages are stored **AES-256-GCM encrypted** — even a stolen database reveals nothing readable.  
Authentication uses **JWT tokens** and passwords are hashed with **bcrypt** (one-way, never stored in plain text).

### 🔑 How It Works

| Step | Endpoint | What happens |
|------|----------|-------------|
| 1️⃣ Register | `POST /register` | Password is bcrypt-hashed and stored. The original is gone. |
| 2️⃣ Login | `POST /login` | Hash is verified → a signed JWT token is returned. |
| 3️⃣ Send message | `POST /messages` | Message is AES-256-GCM encrypted before hitting the DB. |
| 4️⃣ Read messages | `GET /messages` | Ciphertext is decrypted on the fly and returned as plain text. |

### 🗄️ What Lives in the Database

| Table | Column | Stored as | Readable by a thief? |
|-------|--------|-----------|----------------------|
| `users` | `username` | `alice` | ✅ Yes (not secret) |
| `users` | `password_hash` | `$2b$12$eImiTXuW...` | ❌ No — one-way fingerprint |
| `messages` | `sender` / `recipient` | `alice`, `bob` | ✅ Yes (not secret) |
| `messages` | `ciphertext` | `aGVsbG8gd29ybGQ...` | ❌ No — AES encrypted |

### 📁 Project Structure

```
apps/messenger/
├── server/
│   ├── main.py          # 🚀 FastAPI app entry point
│   ├── models.py        # 🗄️  SQLAlchemy DB models (users, messages)
│   ├── auth.py          # 🔑 bcrypt hashing + JWT functions
│   ├── routes.py        # 🛣️  API route handlers
│   ├── crypto.py        # 🔒 AES-256-GCM encrypt/decrypt (given)
│   ├── schemas.py       # 📋 Pydantic request/response schemas (given)
│   ├── dependencies.py  # 🔗 FastAPI dependency injection
│   ├── repositories.py  # 📦 DB query helpers
│   └── broadcaster.py   # 📡 SSE event broadcaster (Stage 2+)
├── migrations/          # 🗂️  Alembic DB migrations
├── static/
│   └── index.html       # 🌐 Basic web client
├── tests/
│   └── test_app.py      # 🧪 Pytest test suite
├── client.py            # 🖥️  CLI test client
└── requirements.txt
```

### ⚙️ Tech Stack

- **FastAPI** — async REST framework
- **SQLAlchemy** — ORM + SQLite
- **bcrypt** — password hashing
- **python-jose** — JWT signing & verification
- **cryptography** — AES-256-GCM message encryption
- **Alembic** — database migrations

### 🚀 Quick Start

```bash
cd apps/messenger
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
uvicorn server.main:app --reload
```

> 🌐 API: http://localhost:8000  
> 📖 Interactive docs: http://localhost:8000/docs

### ✅ Verification Checklist (Stage 1)

```
1.  POST /register   { "username": "alice", "password": "secret123" }  → 201 Created
2.  POST /register   (same again)                                       → 400 Bad Request
3.  POST /login      { "username": "alice", "password": "secret123" }  → 200 OK + token
4.  GET  /messages   (no token)                                         → 403 Forbidden
5.  GET  /messages   (fake token)                                       → 401 Unauthorized
6.  POST /messages   { "content": "hello bob", "recipient": "bob" }    → 201 Created
7.  GET  /messages   (valid token)                                      → plain text messages
8.  Open messenger.db → ciphertext column is unreadable gibberish      ✅
9.  pytest tests/ -v                                                    → all tests pass ✅
```

### 🧪 Running Tests

```bash
cd apps/messenger
pytest tests/ -v
```

---

## �️ Project Structure

```
secure-management-platform/
├── apps/
│   └── messenger/   # 💬 Secure messaging API (FastAPI + SQLite)
└── README.md
```

---

## 🔐 Security Highlights

| Feature | Implementation |
|---------|---------------|
| 🔑 Password storage | bcrypt one-way hashing — original never stored |
| 🎫 Authentication | JWT tokens — signed, expiry-aware, stateless |
| 🔒 Message encryption | AES-256-GCM — tamper-evident, nonce-per-message |
| 🚫 Unauthorized access | HTTP 401/403 on all protected endpoints |
| 🗃️ Stolen DB protection | Only hashes and ciphertext — no readable secrets |
