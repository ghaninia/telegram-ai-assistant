"""Knowledge base: facts the bot may use when replying (prices, opening hours, ...)."""

import sqlite3

from telegram_ai_bot.core.models import KnowledgeItem
from telegram_ai_bot.storage.database import Database


def _to_item(row: sqlite3.Row) -> KnowledgeItem:
    return KnowledgeItem(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        enabled=bool(row["enabled"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class KnowledgeRepository:
    def __init__(self, db: Database):
        self._db = db

    def list(self, query: str = "") -> list[KnowledgeItem]:
        sql, params = "SELECT * FROM knowledge", ()
        if query:
            sql += " WHERE title LIKE ? OR content LIKE ?"
            params = (f"%{query}%", f"%{query}%")
        with self._db.connect() as conn:
            rows = conn.execute(sql + " ORDER BY id DESC", params).fetchall()
        return [_to_item(r) for r in rows]

    def enabled(self) -> list[KnowledgeItem]:
        with self._db.connect() as conn:
            rows = conn.execute("SELECT * FROM knowledge WHERE enabled = 1 ORDER BY id").fetchall()
        return [_to_item(r) for r in rows]

    def count_enabled(self) -> int:
        with self._db.connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM knowledge WHERE enabled = 1").fetchone()[0]

    def get(self, item_id: int) -> KnowledgeItem | None:
        with self._db.connect() as conn:
            row = conn.execute("SELECT * FROM knowledge WHERE id = ?", (item_id,)).fetchone()
        return _to_item(row) if row else None

    def add(self, title: str, content: str, enabled: bool = True) -> int:
        with self._db.connect() as conn:
            cur = conn.execute(
                "INSERT INTO knowledge (title, content, enabled) VALUES (?, ?, ?)",
                (title, content, int(enabled)),
            )
            return cur.lastrowid

    def update(self, item_id: int, title: str, content: str, enabled: bool) -> None:
        with self._db.connect() as conn:
            conn.execute(
                "UPDATE knowledge SET title = ?, content = ?, enabled = ?, "
                "updated_at = datetime('now', 'localtime') WHERE id = ?",
                (title, content, int(enabled), item_id),
            )

    def set_enabled(self, item_id: int, enabled: bool) -> None:
        with self._db.connect() as conn:
            conn.execute("UPDATE knowledge SET enabled = ? WHERE id = ?", (int(enabled), item_id))

    def delete(self, item_id: int) -> None:
        with self._db.connect() as conn:
            conn.execute("DELETE FROM knowledge WHERE id = ?", (item_id,))
