"""
broadcaster.py — In-memory pub/sub broadcaster for SSE connections.

╔══════════════════════════════════════════════╗
║  YOUR TASK: implement the three methods.     ║
╚══════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONCEPT 1 — OBSERVER PATTERN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  The Observer pattern defines a one-to-many dependency:
  when one object (the subject) changes state, all of its
  dependents (observers) are notified automatically.

  Here:
    Subject   = the Broadcaster
    Observers = one asyncio.Queue cted SSE client

  Each connected client owns a Queue (its personal mailbox).
  When POST /messages is called, broadcast() drops a copy of
  the message JSON into every queue registered for the recipient.
  The /stream route is waiting on queue.get() — it wakes up
  instantly and streams the event to the browser/client.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONCEPT 2 — THREAD-SAFE BRIDGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  POST /messages is a *synchronous* route — FastAPI runs it
  in a thread-pool worker, NOT on the asyncio event loop thread.

  asyncio.Queue is not thread-safe. Calling queue.put_nowait()
  directly from a worker thread is a race condition.

  The fix: loop.call_soon_threadsafe(queue.put_nowait, data)

  This schedules the put on the event-loop thread — safe, fast,
  and requires no await (put_nowait is not a coroutine).

  Anatomy:
    asyncio.get_event_loop()  → get the running event loop
    loop.call_soon_threadsafe(fn, *args)
                              → schedule fn(*args) on that loop,
                                from any thread, safely
"""

import asyncio
from collections import defaultdict
from typing import DefaultDict


class Broadcaster:
    """
    In-memory event broadcaster (Observer pattern).

    One instance is created at import time in dependencies.py and
    shared for the entire application lifetime.  Each connected SSE
    client subscribes a Queue; broadcast() wakes them all up.
    """

    def __init__(self) -> None:
        # username → list of Queues (one per active SSE connection)
        self._subscribers: DefaultDict[str, list[asyncio.Queue]] = defaultdict(list)
        self._loop: asyncio.AbstractEventLoop | None = None

    # -----------------------------------------------------------------------
    # TODO 1 — Register a new SSE listener for a username
    # -----------------------------------------------------------------------
    def subscribe(self, username: str) -> asyncio.Queue:
        """
        Create a fresh asyncio.Queue for this connection, record it in
        self._subscribers[username], and return it.

        The /stream route will call:
            queue = broadcaster.subscribe(username)
            data  = await queue.get()   # blocks until a message arrives
        """
        if self._loop is None:
            self._loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[username].append(queue)
        return queue

    # -----------------------------------------------------------------------
    # TODO 2 — Remove a listener when its SSE connection closes
    # -----------------------------------------------------------------------
    def unsubscribe(self, username: str, queue: asyncio.Queue) -> None:
        """
        Remove `queue` from self._subscribers[username].
        Swallow ValueError — the queue may have already been removed
        if the connection dropped unexpectedly.
        """
        try:
            self._subscribers[username].remove(queue)
        except ValueError:
            pass

    # -----------------------------------------------------------------------
    # TODO 3 — Push an event to every active listener for a username
    # -----------------------------------------------------------------------
    def broadcast(self, username: str, data: str) -> None:
        """
        Deliver `data` (a JSON string) to every Queue registered under
        `username`.

        IMPORTANT: this method is called from a *synchronous* route
        handler that runs in a thread pool.  You cannot use `await`
        here.  Use the thread-safe bridge instead:

            loop = asyncio.get_event_loop()
            for queue in list(self._subscribers[username]):
                loop.call_soon_threadsafe(queue.put_nowait, data)

        list(...) creates a snapshot — safe if a subscriber unregisters
        mid-iteration.
        """
        if self._loop is None:
            return
        for queue in list(self._subscribers[username]):
            self._loop.call_soon_threadsafe(queue.put_nowait, data)
