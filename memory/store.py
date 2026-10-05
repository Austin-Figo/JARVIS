"""Persistent memory storage for JARVIS using SQLite."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class MemoryStore:
    """Thread-safe SQLite-backed memory store."""

    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            db_path = Path(__file__).resolve().parents[1] / "memory" / "jarvis_memory.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path
        self._lock = threading.RLock()
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '[]',
                    timestamp INTEGER NOT NULL,
                    synced INTEGER NOT NULL DEFAULT 0,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_tags ON memories(tags)
            """)
            conn.commit()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "title": row["title"],
            "content": row["content"],
            "tags": json.loads(row["tags"]),
            "timestamp": row["timestamp"],
            "synced": bool(row["synced"]),
        }

    def add(self, title: str, content: str, tags: list[str] | None = None, synced: bool = False) -> dict[str, Any]:
        """Add a new memory entry."""
        now = int(time.time() * 1000)
        memory_id = f"mem_{now}_{threading.get_ident()}"
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memories (id, title, content, tags, timestamp, synced, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (memory_id, title, content, json.dumps(tags or []), now, int(synced), now, now),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
            return self._row_to_dict(row)

    def get(self, memory_id: str) -> dict[str, Any] | None:
        """Get a memory by ID."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
            return self._row_to_dict(row) if row else None

    def list(
        self,
        limit: int = 100,
        offset: int = 0,
        query: str | None = None,
        tag: str | None = None,
    ) -> list[dict[str, Any]]:
        """List memories with optional filtering."""
        sql = "SELECT * FROM memories WHERE 1=1"
        params: list[Any] = []

        if query:
            sql += " AND (title LIKE ? OR content LIKE ?)"
            like = f"%{query}%"
            params.extend([like, like])

        if tag:
            sql += " AND tags LIKE ?"
            params.append(f'%"{tag}"%')

        sql += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def update(self, memory_id: str, **fields) -> bool:
        """Update a memory entry."""
        allowed = {"title", "content", "tags", "synced"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = list(updates.values())
        if "tags" in updates:
            params[params.index(updates["tags"])] = json.dumps(updates["tags"])
        params.append(int(time.time() * 1000))  # updated_at
        params.append(memory_id)

        with self._lock, self._connect() as conn:
            cur = conn.execute(
                f"UPDATE memories SET {set_clause}, updated_at = ? WHERE id = ?",
                params,
            )
            conn.commit()
            return cur.rowcount > 0

    def delete(self, memory_id: str) -> bool:
        """Delete a memory entry."""
        with self._lock, self._connect() as conn:
            cur = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            return cur.rowcount > 0

    def get_all_tags(self) -> list[str]:
        """Get all unique tags across memories."""
        with self._connect() as conn:
            rows = conn.execute("SELECT tags FROM memories").fetchall()
            tags = set()
            for row in rows:
                try:
                    tags.update(json.loads(row["tags"]))
                except Exception:
                    pass
            return sorted(tags)

    def count(self) -> int:
        """Get total memory count."""
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

    def seed_initial(self, memories: list[dict[str, Any]]) -> None:
        """Seed initial memories if database is empty."""
        if self.count() > 0:
            return
        now = int(time.time() * 1000)
        with self._lock, self._connect() as conn:
            for i, m in enumerate(memories):
                mem_id = m.get("id") or f"seed_{i}"
                conn.execute(
                    """
                    INSERT OR IGNORE INTO memories (id, title, content, tags, timestamp, synced, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        mem_id,
                        m["title"],
                        m["content"],
                        json.dumps(m.get("tags", [])),
                        int(m.get("timestamp", now)),
                        int(m.get("synced", False)),
                        now,
                        now,
                    ),
                )
            conn.commit()