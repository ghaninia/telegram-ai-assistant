import sqlite3

from telegram_ai_bot.core.prompts import DEFAULT_SYSTEM_PROMPT
from telegram_ai_bot.storage.database import MIGRATIONS, Database
from telegram_ai_bot.storage.knowledge import KnowledgeRepository
from telegram_ai_bot.storage.settings import AppSettings, SettingsRepository


def test_knowledge_crud_and_search(db):
    repo = KnowledgeRepository(db)
    hours = repo.add("Hours", "9 to 6")
    address = repo.add("Address", "Tehran", enabled=False)

    assert [i.title for i in repo.search()] == ["Address", "Hours"]  # newest first
    assert [i.title for i in repo.search("Tehran")] == ["Address"]
    assert [i.title for i in repo.enabled()] == ["Hours"]
    assert repo.count_enabled() == 1

    repo.update(hours, "Opening hours", "9 to 7", enabled=False)
    repo.set_enabled(address, True)
    assert repo.get(hours).title == "Opening hours"
    assert not repo.get(hours).enabled
    assert [i.title for i in repo.enabled()] == ["Address"]

    repo.delete(address)
    assert repo.get(address) is None


def test_settings_defaults_and_round_trip(db):
    repo = SettingsRepository(db)
    assert repo.load() == AppSettings()

    saved = AppSettings(api_key="k", model="m", fallback_models=("a", "b"), proxy="socks5://h:1",
                        system_prompt="custom")
    repo.save(saved)
    assert repo.load() == saved
    assert saved.models == ["m", "a", "b"]


def test_unchanged_default_prompt_is_not_pinned(db):
    repo = SettingsRepository(db)
    repo.save(AppSettings(system_prompt=DEFAULT_SYSTEM_PROMPT))
    with db.connect() as conn:
        stored = conn.execute("SELECT value FROM settings WHERE key = 'system_prompt'").fetchone()[0]
    assert stored == ""
    assert repo.load().system_prompt == DEFAULT_SYSTEM_PROMPT


def test_empty_fallback_list_is_preserved(db):
    repo = SettingsRepository(db)
    repo.save(AppSettings(fallback_models=()))
    assert repo.load().fallback_models == ()


def test_upgrades_database_from_previous_release(tmp_path):
    """Databases created before migrations existed (user_version 0) keep their data."""
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(MIGRATIONS[0])
        conn.execute("INSERT INTO knowledge (title, content) VALUES ('t', 'c')")
        conn.execute("INSERT INTO settings (key, value) VALUES ('api_key', 'legacy-key')")
    conn.close()

    db = Database(path)
    assert KnowledgeRepository(db).search()[0].title == "t"
    assert SettingsRepository(db).load().api_key == "legacy-key"
    with db.connect() as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == len(MIGRATIONS)
