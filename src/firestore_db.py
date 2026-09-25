"""Firestore storage for tasks. Same functions as db.py, used when STORAGE=firestore.

Tasks live in the "tasks" collection, one document per task, keyed by its id.
Ids stay integers (like SQLite) via a counter document updated in a transaction.
"""

from datetime import datetime, timezone

from google.api_core.exceptions import NotFound
from google.cloud import firestore

_client: firestore.Client | None = None


def _db() -> firestore.Client:
    global _client
    if _client is None:
        _client = firestore.Client()  # project + credentials come from Cloud Run automatically
    return _client


def _tasks():
    return _db().collection("tasks")


def init_db() -> None:
    _db()  # Firestore needs no schema; just make sure the client can be created


def list_tasks() -> list[dict]:
    return [doc.to_dict() for doc in _tasks().order_by("id").stream()]


def create_task(title: str) -> dict:
    client = _db()
    counter = client.collection("meta").document("task_counter")

    @firestore.transactional
    def _create(transaction) -> dict:
        snap = counter.get(transaction=transaction)
        next_id = (snap.get("last_id") if snap.exists else 0) + 1
        task = {
            "id": next_id,
            "title": title,
            "done": False,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        transaction.set(counter, {"last_id": next_id})
        transaction.set(_tasks().document(str(next_id)), task)
        return task

    return _create(client.transaction())


def update_task(task_id: int, title: str | None = None, done: bool | None = None) -> dict | None:
    """Apply whichever fields are given. Returns None if the task doesn't exist."""
    ref = _tasks().document(str(task_id))
    changes = {k: v for k, v in (("title", title), ("done", done)) if v is not None}
    if changes:
        try:
            ref.update(changes)
        except NotFound:
            return None
    snap = ref.get()
    return snap.to_dict() if snap.exists else None


def delete_task(task_id: int) -> bool:
    ref = _tasks().document(str(task_id))
    if not ref.get().exists:
        return False
    ref.delete()
    return True
