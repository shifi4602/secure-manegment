"""
client.py — Terminal chat client for Secure Messenger.

╔══════════════════════════════════════════════╗
║  YOUR TASK: implement the three functions.   ║
╚══════════════════════════════════════════════╝

HOW TO RUN:
  python client.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONCEPT 1 — CONCURRENT I/O WITH THREADS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  The client needs to do two things at the same time:
    1. Wait for the user to type a message  (blocks forever)
    2. Listen for incoming SSE events       (also blocks forever)

  If you tried both sequentially, typing would block the listener
  and vice versa — the program would miss incoming messages
  while waiting for input.

  The solution: two threads.

    Main thread     → reads input(), sends messages
    Listener thread → connects to GET /stream, prints events

  The listener thread is a daemon thread (daemon=True).
  Python exits as soon as the main thread finishes, without
  waiting for daemon threads — perfect for background listeners.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONCEPT 2 — READING SSE WITH HTTPX STREAMING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SSE is just a long HTTP response that the server never closes.
  New lines arrive one at a time, formatted like:

      data: {"id": 1, "sender": "alice", "content": "hello", ...}
      (blank line)
      data: {"id": 2, ...}

  httpx supports streaming responses via a context manager:

      with httpx.stream("GET", url, headers=..., timeout=None) as r:
          for line in r.iter_lines():
              if line.startswith("data: "):
                  payload = json.loads(line[6:])
                  ...

  timeout=None is important — you don't want httpx to time out a
  connection that is intentionally open forever.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEMO WORKFLOW (two terminals)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Terminal 1:  python client.py   → username: alice, chat with: bob
  Terminal 2:  python client.py   → username: bob,   chat with: alice

  Type in terminal 1 → message appears instantly in terminal 2.
  No polling. No delay.
"""

import getpass
import json
import sys
import threading

import httpx


BASE_URL = "http://127.0.0.1:8000"


def login(username: str, password: str) -> str:
    """
    Try to register (ignores 400 if user already exists), then log in.
    Returns the JWT access token.  Exits the program on login failure.
    """
    httpx.post(f"{BASE_URL}/register", json={"username": username, "password": password})
    response = httpx.post(
        f"{BASE_URL}/login",
        json={"username": username, "password": password},
    )
    if response.status_code != 200:
        print(f"Login failed: {response.json().get('detail', response.text)}")
        sys.exit(1)
    return response.json()["access_token"]


# ---------------------------------------------------------------------------
# TODO 1 — Send a message to a recipient
# ---------------------------------------------------------------------------
def send_message(token: str, recipient: str, content: str) -> None:
    """
    POST /messages with the Bearer token in the Authorization header
    and {"recipient": ..., "content": ...} as the JSON body.

    Print a short confirmation on success, or the error detail on failure.

    Hint:
        response = httpx.post(
            f"{BASE_URL}/messages",
            json={"recipient": recipient, "content": content},
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 201:
            print(f"  [sent]", flush=True)
        else:
            print(f"  [error] {response.json().get('detail', response.text)}", flush=True)
    """
    response = httpx.post(
        f"{BASE_URL}/messages",
        json={"recipient": recipient, "content": content},
        headers={"Authorization": f"Bearer {token}"},
    )
    if response.status_code == 201:
        print("  [sent]", flush=True)
    else:
        print(f"  [error] {response.json().get('detail', response.text)}", flush=True)


# ---------------------------------------------------------------------------
# TODO 2 — Listen to the SSE stream and print incoming messages
# ---------------------------------------------------------------------------
def listen_stream(token: str, my_username: str) -> None:
    """
    Open a streaming GET /stream connection and loop forever, printing
    each incoming message as it arrives.

    This function runs in a daemon thread — it must never return normally.
    If tction drops, reconnect after a short delay.

    SSE lines to handle:
      • lines starting with "data: " → parse JSON and print the message
      • blank lines and ": keep-alive" comments → ignore

    Print format (suggestion):
        \\n[alice → you]: hello there

    Hint:
        with httpx.stream(
            "GET", f"{BASE_URL}/stream",
            headers={"Authorization": f"Bearer {token}"},
            timeout=None,
        ) as r:
            for line in r.iter_lines():
                if line.startswith("data: "):
                    payload = json.loads(line[6:])
                    sender  = payload["sender"]
                    content = payload["content"]
                    print(f"\\n[{sender} → you]: {content}", flush=True)
    """
    while True:
        try:
            with httpx.stream(
                "GET",
                f"{BASE_URL}/stream",
                headers={"Authorization": f"Bearer {token}"},
                timeout=None,
            ) as r:
                for line in r.iter_lines():
                    if line.startswith("data: "):
                        payload = json.loads(line[6:])
                        sender = payload["sender"]
                        content = payload["content"]
                        print(f"\n[{sender} → you]: {content}", flush=True)
        except Exception:
            import time
            time.sleep(2)


# ---------------------------------------------------------------------------
# TODO 3 — Wire everything together
# ---------------------------------------------------------------------------
def main() -> None:
    """
    1. Prompt for username, password (hidden), and the recipient to chat with.
    2. Call login() to obtain a JWT token.
    3. Start a daemon thread running listen_stream(token, username).
    4. Print usage instructions.
    5. Enter a loop: read a line from input(), send it with send_message().
       Handle KeyboardInterrupt (Ctrl+C) gracefully.

    Hint:
        username  = input("Username : ").strip()
        password  = getpass.getpass("Password : ")
        recipient = input("Chat with: ").strip()

        print("Logging in...")
        token = login(username, password)
        print(f"Connected as {username!r}. Chatting with {recipient!r}.")
        print("Type a message and press Enter.  Ctrl+C to quit.\\n")

        t = threading.Thread(target=listen_stream, args=(token, username), daemon=True)
        t.start()

        try:
            while True:
                content = input()
                if content.strip():
                    send_message(token, recipient, content)
        except (KeyboardInterrupt, EOFError):
            print("\\nGoodbye.")
    """
    username = input("Username : ").strip()
    password = getpass.getpass("Password : ")
    recipient = input("Chat with: ").strip()

    print("Logging in...")
    token = login(username, password)
    print(f"Connected as {username!r}. Chatting with {recipient!r}.")
    print("Type a message and press Enter.  Ctrl+C to quit.\n")

    t = threading.Thread(target=listen_stream, args=(token, username), daemon=True)
    t.start()

    try:
        while True:
            content = input()
            if content.strip():
                send_message(token, recipient, content)
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye.")


if __name__ == "__main__":
    main()
