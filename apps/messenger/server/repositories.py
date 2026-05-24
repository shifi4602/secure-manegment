"""
repositories.py — Data access layer (Repository pattern).

╔══════════════════════════════════════════════╗
║  YOUR TASK: implement the four methods.      ║
╚══════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONCEPT — REPOSITORY PATTERN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Without this pattern, routes mix HTTP logic with database
  queries:

    @router.post("/login")
    def login(body, db = Depends(get_db)):
        user = db.query(User).filter(User.username == body.username).first()
        if not user or not verify_password(body.password, user.password_hash):
            raise HTTPException(401, ...)

  The route handler now knows about SQLAlchemy, the User model,
  *and* how to query it — three different concerns tangled together.

  The Repository pattern separates data access behind a clean
  interface:

    @router.post("/login")
    def login(body, repo = Depends(get_user_repo)):
        user = repo.find_by_username(body.username)
        if not user or not verify_password(body.password, user.password_hash):
            raise HTTPException(401, ...)

  The route only asks "find me this user" — it doesn't know (or care)
  whether the data comes from SQLAlchemy, MongoDB, or a cache.

  Benefits:
    • Routes become thin HTTP adapters (easier to read)
    • Swapping the database only changes the repository
    • Tests can mock the repository without touching HTTP at all
"""

from typing import Optional

from sqlalchemy.orm import Session

from .models import User, Message


class UserRepository:
    """All database operations involving the `users` table."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # -----------------------------------------------------------------------
    # TODO 1 — Look up a user by username
    # -----------------------------------------------------------------------
    def find_by_username(self, username: str) -> Optional[User]:
        """
        Return the User row whose username matches, or None if not found.

        Hint:
            return self.db.query(User).filter(User.username == username).first()
        """
        raise NotImplementedError

    # -----------------------------------------------------------------------
    # TODO 2 — Create and persist a new user
    # -----------------------------------------------------------------------
    def create(self, username: str, password_hash: str) -> User:
        """
        Build a User ORM object, add it to the session, commit, and return it.

        Hint:
            user = User(username=username, password_hash=password_hash)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        """
        raise NotImplementedError


class MessageRepository:
    """All database operations involving the `messages` table."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # -----------------------------------------------------------------------
    # TODO 3 — Persist a new message
    # -----------------------------------------------------------------------
    def create(self, sender: str, recipient: str, ciphertext: str) -> Message:
        """
        Build a Message ORM object, add it, commit, refresh (so that
        created_at is populated by the DB default), and return it.

        Hint:
            msg = Message(sender=sender, recipient=recipient, ciphertext=ciphertext)
            self.db.add(msg)
            self.db.commit()
            self.db.refresh(msg)
            return msg
        """
        raise NotImplementedError

    # -----------------------------------------------------------------------
    # TODO 4 — Fetch all messages relevant to a user
    # -----------------------------------------------------------------------
    def find_by_user(self, username: str) -> list[Message]:
        """
        Return every message where sender == username OR recipient == username,
        ordered by created_at ascending (oldest first).

        Hint — use the | operator to combine SQLAlchemy filter conditions:
            return (
                self.db.query(Message)
                .filter(
                    (Message.sender == username) | (Message.recipient == username)
                )
                .order_by(Message.created_at)
                .all()
            )
        """
        raise NotImplementedError
