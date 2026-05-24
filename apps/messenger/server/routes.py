"""
routes.py — All API route handlers.

╔══════════════════════════════════════════════╗
║  YOUR TASK: implement the four routes.       ║
╚══════════════════════════════════════════════╝

WHY A SEPARATE routes.py?
  In real projects, main.py only creates the app and wires things together.
  The actual logic lives in dedicated files — one per feature area.
  This keeps files small, focused, and easy to navigate.
  main.py imports this router and registers it with one line.

THE FOUR ROUTES YOU NEED TO IMPLEMENT:

  ┌─────────────────────────────────────────────────────────────────────┐
  │ POST /register                                                      │
  │   Receives: RegisterRequest (username, password)                    │
  │   1. Check if the username is already taken → return 400 if so     │
  │   2. Hash the password (NEVER store plain text)                     │
  │   3. Save the new User to the database                              │
  │   4. Return a success message                                       │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │ POST /login                                                         │
  │   Receives: LoginRequest (username, password)                       │
  │   1. Find the user in the database → return 401 if not found       │
  │   2. Verify the password against the stored hash → 401 if wrong    │
  │   3. Create and return a JWT token                                  │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │ POST /messages                          [requires valid JWT]        │
  │   Receives: SendMessageRequest (content, recipient)                 │
  │   1. Encrypt the content with encrypt()                             │
  │   2. Save a new Message row (sender=current user, recipient=...)    │
  │   3. Return the message as MessageResponse (with decrypted content) │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │ GET /messages                           [requires valid JWT]        │
  │   1. Fetch all messages from the database                           │
  │   2. Decrypt each message's ciphertext before returning             │
  │   3. Return a list of MessageResponse objects                       │
  │                                                                     │
  │   THINK ABOUT: should a user see ALL messages, or only those        │
  │   where they are the sender or recipient?                           │
  └─────────────────────────────────────────────────────────────────────┘

USEFUL IMPORTS ALREADY PROVIDED BELOW.
USEFUL PATTERN — how to query the database:
  user = db.query(User).filter(User.username == "alice").first()
  messages = db.query(Message).order_by(Message.created_at).all()

USEFUL PATTERN — how to save a new row:
  new_user = User(username="alice", password_hash="$2b$...")
  db.add(new_user)
  db.commit()
  db.refresh(new_user)   ← fills in the auto-generated id and created_at
"""

import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from .models import User, Message, get_db
from .schemas import (
    RegisterRequest, LoginRequest, TokenResponse,
    SendMessageRequest, MessageResponse,
)
from .auth import hash_password, verify_password, create_token, decode_token, require_auth
from .crypto import encrypt, decrypt
from .dependencies import get_broadcaster
from .broadcaster import Broadcaster


log = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# TODO 1 — Register a new user
# ---------------------------------------------------------------------------
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    user = User(username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    log.info("New user registered: %s", body.username)
    return {"message": "User registered successfully"}


# ---------------------------------------------------------------------------
# TODO 2 — Login and receive a JWT token
# ---------------------------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_token(user.username)
    log.info("User logged in: %s", user.username)
    return TokenResponse(access_token=token)


# ---------------------------------------------------------------------------
# TODO 3 — Send a message (authenticated)
# ---------------------------------------------------------------------------
@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    username: str = Depends(require_auth),
    broadcaster: Broadcaster = Depends(get_broadcaster),
):
    ciphertext = encrypt(body.content)
    message = Message(sender=username, recipient=body.recipient, ciphertext=ciphertext)
    db.add(message)
    db.commit()
    db.refresh(message)
    log.info("Message sent: %s → %s", username, body.recipient)
    response = MessageResponse(
        id=message.id,
        sender=message.sender,
        recipient=message.recipient,
        content=body.content,
        created_at=message.created_at,
    )
    broadcaster.broadcast(body.recipient, json.dumps(response.model_dump(mode="json")))
    return response


# ---------------------------------------------------------------------------
# TODO 4 — Fetch messages (authenticated)
# ---------------------------------------------------------------------------
@router.get("/messages", response_model=list[MessageResponse])
def get_messages(
    db: Session = Depends(get_db),
    username: str = Depends(require_auth),
):
    messages = (
        db.query(Message)
        .filter((Message.sender == username) | (Message.recipient == username))
        .order_by(Message.created_at)
        .all()
    )
    return [
        MessageResponse(
            id=m.id,
            sender=m.sender,
            recipient=m.recipient,
            content=decrypt(m.ciphertext),
            created_at=m.created_at,
        )
        for m in messages
    ]


# ---------------------------------------------------------------------------
# GET /users — list all other registered users (authenticated)
# ---------------------------------------------------------------------------
@router.get("/users", response_model=list[str])
def list_users(
    db: Session = Depends(get_db),
    username: str = Depends(require_auth),
):
    users = db.query(User).filter(User.username != username).all()
    return [u.username for u in users]


# ---------------------------------------------------------------------------
# GET /stream — SSE push stream (authenticated)
# ---------------------------------------------------------------------------
@router.get("/stream")
async def stream_events(
    broadcaster: Broadcaster = Depends(get_broadcaster),
    token: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
):
    # Accept token from ?token= (browser EventSource) or Authorization header (CLI)
    raw = token
    if not raw and authorization and authorization.lower().startswith("bearer "):
        raw = authorization.split(" ", 1)[1]
    username = decode_token(raw) if raw else None
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    queue = broadcaster.subscribe(username)

    async def generator():
        try:
            while True:
                data = await queue.get()
                yield {"data": data}
        finally:
            broadcaster.unsubscribe(username, queue)

    return EventSourceResponse(generator())
