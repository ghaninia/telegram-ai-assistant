"""SQLite connection handling and schema migrations."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path

# Each entry upgrades the schema by one version (tracked in PRAGMA user_version).
# Statements use IF NOT EXISTS so databases created by earlier releases upgrade cleanly.
MIGRATIONS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS knowledge (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        title      TEXT    NOT NULL,
        content    TEXT    NOT NULL,
        enabled    INTEGER NOT NULL DEFAULT 1,
        created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
    );
    CREATE TABLE IF NOT EXISTS settings (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """,
)


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.migrate()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Short-lived connection that commits on success and rolls back on error."""
        with closing(sqlite3.connect(self.path)) as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                yield conn

    def migrate(self) -> None:
        with self.connect() as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            for target, script in enumerate(MIGRATIONS[version:], start=version + 1):
                conn.executescript(script)
                conn.execute(f"PRAGMA user_version = {target}")
