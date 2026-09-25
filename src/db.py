"""All SQLite access for tasks lives here."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tasks.db"


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        with conn:  # commits on success, rolls back on error
            yield conn
    finally:
        conn.close()


def _to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
        "created_at": row["created_at"],
    }


def init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT    NOT NULL,
                done       INTEGER NOT NULL DEFAULT 0,
                created_at TEXT    NOT NULL
            )
            """
        )


def list_tasks() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    return [_to_dict(r) for r in rows]


def create_task(title: str) -> dict:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, done, created_at) VALUES (?, 0, ?)",
            (title, now),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _to_dict(row)


def update_task(task_id: int, title: str | None = None, done: bool | None = None) -> dict | None:
    """Apply whichever fields are given. Returns None if the task doesn't exist."""
    with _connect() as conn:
        if title is not None:
            conn.execute("UPDATE tasks SET title = ? WHERE id = ?", (title, task_id))
        if done is not None:
            conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (int(done), task_id))
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _to_dict(row) if row else None


def delete_task(task_id: int) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return cur.rowcount > 0
