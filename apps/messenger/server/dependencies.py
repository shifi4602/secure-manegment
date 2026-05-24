"""
dependencies.py — Dependency injection wiring.

╔══════════════════════════════════════════════════════════════╗
║  THIS FILE IS COMPLETE — you do not need to change anything. ║
╚══════════════════════════════════════════════════════════════╝

This is the single place where concrete instances are created and
handed to FastAPI's dependency injection system.

Routes never import Broadcaster or Repository classes directly —
they declare what they need via Depends(), and FastAPI calls the
provider functions here to supply the correct instance.

Why this matters:

  1. Testability — tests override get_broadcaster() to inject a
     fresh Broadcaster() so SSE tests are isolated from each other.

        app.dependency_overrides[get_broadcaster] = lambda: Broadcaster()

  2. Single source of truth — changing the broadcaster implementation
     (e.g., swapping in-memory for Redis pub/sub) happens in one place.

  3. Thin routes — route signatures look like:
        def send_message(
            broadcaster: Broadcaster = Depends(get_broadcaster),
            repo: MessageRepository  = Depends(get_message_repo),
        ):
     ... instead of constructing objects inside route bodies.
"""

from sqlalchemy.orm import Session
from fastapi import Depends

from .models import get_db
from .broadcaster import Broadcaster
from .repositories import UserRepository, MessageRepository


# ---------------------------------------------------------------------------
# Broadcaster — module-level singleton, one instance for the whole process
# ---------------------------------------------------------------------------

_broadcaster = Broadcaster()


def get_broadcaster() -> Broadcaster:
    """
    Return the shared Broadcaster instance.
    Override in tests via app.dependency_overrides[get_broadcaster].
    """
    return _broadcaster


# ---------------------------------------------------------------------------
# Repositories — new instance per request, each bound to its own DB session
# ---------------------------------------------------------------------------

def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_message_repo(db: Session = Depends(get_db)) -> MessageRepository:
    return MessageRepository(db)
