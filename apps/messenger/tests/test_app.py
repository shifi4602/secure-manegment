"""
test_app.py — Stage 1 test suite.

╔══════════════════════════════════════════════════════════════════════╗
║  YOUR TASK: the test structure is given. Some tests are complete,   ║
║  others have a TODO for you to finish.                              ║
╚══════════════════════════════════════════════════════════════════════╝

HOW TO RUN:
  pytest tests/ -v

HOW TESTS WORK HERE:
  We use FastAPI's TestClient — it sends real HTTP requests to your app
  without needing to start a server. Each test gets a fresh, empty
  database so tests never interfere with each other.

  The test database is a separate file (test_messenger.db) and is
  wiped clean before every single test.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.main import app
from server.models import Base, get_db
from server.crypto import encrypt, decrypt


# ---------------------------------------------------------------------------
# Test database setup — uses a separate file, wiped before each test
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite:///./test_messenger.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_and_login(client, username="alice", password="secret123") -> str:
    """Register a user and return their JWT token."""
    client.post("/register", json={"username": username, "password": password})
    response = client.post("/login", json={"username": username, "password": password})
    return response.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# 1. Authentication tests
# ===========================================================================

class TestAuthentication:

    def test_register_success(self, client):
        response = client.post("/register", json={"username": "alice", "password": "secret123"})
        assert response.status_code == 201

    def test_register_duplicate_username(self, client):
        client.post("/register", json={"username": "alice", "password": "secret123"})
        response = client.post("/register", json={"username": "alice", "password": "other-password"})
        assert response.status_code == 400

    def test_register_password_too_short(self, client):
        response = client.post("/register", json={"username": "alice", "password": "abc"})
        assert response.status_code == 422   # Pydantic rejects it before your code runs

    def test_login_success(self, client):
        client.post("/register", json={"username": "alice", "password": "secret123"})
        response = client.post("/login", json={"username": "alice", "password": "secret123"})
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self, client):
        client.post("/register", json={"username": "alice", "password": "secret123"})
        response = client.post("/login", json={"username": "alice", "password": "wrongpassword"})
        assert response.status_code == 401

    def test_login_unknown_user(self, client):
        response = client.post("/login", json={"username": "ghost", "password": "secret123"})
        assert response.status_code == 401

    def test_messages_require_token(self, client):
        response = client.get("/messages")
        assert response.status_code in (401, 403)

    def test_messages_reject_bad_token(self, client):
        response = client.get("/messages", headers={"Authorization": "Bearer fake-token"})
        assert response.status_code == 401

    def test_messages_accept_valid_token(self, client):
        token = register_and_login(client)
        response = client.get("/messages", headers=auth(token))
        assert response.status_code == 200


# ===========================================================================
# 2. Encryption tests
# ===========================================================================

class TestEncryption:

    def test_encrypt_is_not_plain_text(self):
        assert encrypt("hello world") != "hello world"

    def test_decrypt_round_trip(self):
        original = "this is a secret message"
        assert decrypt(encrypt(original)) == original

    def test_same_message_encrypts_differently_each_time(self):
        # fresh nonce every call → different ciphertext
        assert encrypt("hello") != encrypt("hello")

    def test_tampered_ciphertext_raises(self):
        blob = encrypt("original")
        tampered = blob[:-4] + "XXXX"
        with pytest.raises(Exception):
            decrypt(tampered)

    # TODO — complete this test:
    # After sending a message via POST /messages, query the database directly
    # and verify that the stored ciphertext is NOT the plain text,
    # but that decrypt(ciphertext) DOES return the original plain text.
    def test_messages_are_stored_encrypted(self, client):
        from server.models import Message
        token = register_and_login(client)
        # send a message
        client.post(
            "/messages",
            json={"content": "hello bob", "recipient": "bob"},
            headers=auth(token),
        )
        # query the DB directly
        db = TestingSession()
        row = db.query(Message).first()
        db.close()
        # assert the ciphertext is not plain text
        assert row.ciphertext != "hello bob"
        # assert decrypt(ciphertext) returns the original
        assert decrypt(row.ciphertext) == "hello bob"


# ===========================================================================
# 3. Messaging tests
# ===========================================================================

class TestMessaging:

    def test_send_message_success(self, client):
        alice_token = register_and_login(client, "alice", "secret123")
        register_and_login(client, "bob", "secret456")

        response = client.post(
            "/messages",
            json={"content": "hello bob", "recipient": "bob"},
            headers=auth(alice_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "hello bob"   # returned decrypted
        assert data["sender"] == "alice"
        assert data["recipient"] == "bob"

    def test_get_messages_returns_decrypted(self, client):
        alice_token = register_and_login(client, "alice", "secret123")
        register_and_login(client, "bob", "secret456")

        client.post("/messages", json={"content": "hi bob", "recipient": "bob"}, headers=auth(alice_token))

        response = client.get("/messages", headers=auth(alice_token))
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) >= 1
        assert messages[0]["content"] == "hi bob"   # must be decrypted, not ciphertext

    # TODO — complete this test:
    # Alice sends a message to Bob. Bob sends a message to Alice.
    # Verify that GET /messages returns ONLY the messages
    # where the requesting user is sender OR recipient.
    def test_user_sees_only_their_messages(self, client):
        alice_token   = register_and_login(client, "alice",   "secret123")
        bob_token     = register_and_login(client, "bob",     "secret456")
        charlie_token = register_and_login(client, "charlie", "secret789")

        # alice → bob
        client.post("/messages", json={"content": "alice to bob",     "recipient": "bob"},   headers=auth(alice_token))
        # charlie → bob  (alice should NOT see this)
        client.post("/messages", json={"content": "charlie to bob",   "recipient": "bob"},   headers=auth(charlie_token))
        # bob → alice  (alice SHOULD see this — she is the recipient)
        client.post("/messages", json={"content": "bob to alice",     "recipient": "alice"}, headers=auth(bob_token))

        response = client.get("/messages", headers=auth(alice_token))
        assert response.status_code == 200
        messages = response.json()

        # alice sees the message she sent and the reply from bob, but not charlie's
        contents = {m["content"] for m in messages}
        assert "alice to bob"   in contents
        assert "bob to alice"   in contents
        assert "charlie to bob" not in contents


# ===========================================================================
# 4. Users endpoint tests
# ===========================================================================

class TestUsers:

    def test_list_users_requires_auth(self, client):
        response = client.get("/users")
        assert response.status_code in (401, 403)

    def test_list_users_rejects_bad_token(self, client):
        response = client.get("/users", headers={"Authorization": "Bearer fake"})
        assert response.status_code == 401

    def test_list_users_excludes_self(self, client):
        alice_token = register_and_login(client, "alice", "secret123")
        register_and_login(client, "bob",     "secret456")
        register_and_login(client, "charlie", "secret789")

        response = client.get("/users", headers=auth(alice_token))
        assert response.status_code == 200
        users = response.json()

        assert "alice"   not in users   # self excluded
        assert "bob"     in users
        assert "charlie" in users

    def test_list_users_empty_when_alone(self, client):
        alice_token = register_and_login(client, "alice", "secret123")

        response = client.get("/users", headers=auth(alice_token))
        assert response.status_code == 200
        assert response.json() == []

    def test_list_users_returns_all_others(self, client):
        alice_token = register_and_login(client, "alice",  "secret123")
        register_and_login(client, "bob",   "secret456")
        register_and_login(client, "carol", "secret789")
        register_and_login(client, "diana", "secret000")

        users = client.get("/users", headers=auth(alice_token)).json()
        assert set(users) == {"bob", "carol", "diana"}


# ===========================================================================
# 5. Multi-recipient sending tests
# ===========================================================================

class TestMultiRecipient:

    def test_send_to_multiple_recipients(self, client):
        """Sender posts separate messages to multiple recipients — all succeed."""
        alice_token = register_and_login(client, "alice",   "secret123")
        register_and_login(client, "bob",     "secret456")
        register_and_login(client, "charlie", "secret789")

        for recipient in ("bob", "charlie"):
            r = client.post(
                "/messages",
                json={"content": "hello everyone", "recipient": recipient},
                headers=auth(alice_token),
            )
            assert r.status_code == 201

        sent = client.get("/messages", headers=auth(alice_token)).json()
        assert len(sent) == 2
        assert all(m["content"] == "hello everyone" for m in sent)

    def test_each_recipient_sees_only_their_own_copy(self, client):
        """Bob and Charlie each receive only the message addressed to them."""
        alice_token   = register_and_login(client, "alice",   "secret123")
        bob_token     = register_and_login(client, "bob",     "secret456")
        charlie_token = register_and_login(client, "charlie", "secret789")

        for recipient in ("bob", "charlie"):
            client.post(
                "/messages",
                json={"content": "broadcast msg", "recipient": recipient},
                headers=auth(alice_token),
            )

        bob_msgs     = client.get("/messages", headers=auth(bob_token)).json()
        charlie_msgs = client.get("/messages", headers=auth(charlie_token)).json()

        assert len(bob_msgs) == 1
        assert bob_msgs[0]["recipient"] == "bob"

        assert len(charlie_msgs) == 1
        assert charlie_msgs[0]["recipient"] == "charlie"

    def test_send_to_all_via_users_endpoint(self, client):
        """Full flow: fetch /users, send to each — mirrors the frontend 'Send to All' button."""
        alice_token = register_and_login(client, "alice",   "secret123")
        register_and_login(client, "bob",     "secret456")
        register_and_login(client, "charlie", "secret789")

        # step 1 — get everyone else (as the frontend does)
        others = client.get("/users", headers=auth(alice_token)).json()
        assert "alice" not in others
        assert set(others) == {"bob", "charlie"}

        # step 2 — send to each
        for user in others:
            r = client.post(
                "/messages",
                json={"content": "msg to all", "recipient": user},
                headers=auth(alice_token),
            )
            assert r.status_code == 201

        # step 3 — alice sees exactly one sent message per recipient
        all_msgs = client.get("/messages", headers=auth(alice_token)).json()
        sent = [m for m in all_msgs if m["sender"] == "alice"]
        assert len(sent) == len(others)
        assert {m["recipient"] for m in sent} == set(others)

    def test_send_to_all_does_not_message_self(self, client):
        """/users never returns the caller, so self-messaging cannot happen."""
        alice_token = register_and_login(client, "alice", "secret123")
        register_and_login(client, "bob", "secret456")

        others = client.get("/users", headers=auth(alice_token)).json()

        # self is never in the list
        assert "alice" not in others

        # even if the frontend tried to send to self (edge-case guard)
        r = client.post(
            "/messages",
            json={"content": "talking to myself", "recipient": "alice"},
            headers=auth(alice_token),
        )
        # the server accepts it (no business rule against it at DB level),
        # but /users would never have suggested it
        assert r.status_code == 201
        msg = r.json()
        assert msg["sender"] == "alice"
        assert msg["recipient"] == "alice"
