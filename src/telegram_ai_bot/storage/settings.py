"""User settings persisted as key/value rows."""

from dataclasses import dataclass

from telegram_ai_bot import config
from telegram_ai_bot.core.prompts import DEFAULT_SYSTEM_PROMPT
from telegram_ai_bot.storage.database import Database


@dataclass(frozen=True, slots=True)
class AppSettings:
    api_key: str = ""
    base_url: str = config.GEMINI_BASE_URL
    model: str = config.GEMINI_MODEL
    fallback_models: tuple[str, ...] = config.GEMINI_FALLBACK_MODELS
    # Used for both Telegram Web and Gemini, e.g. "socks5://127.0.0.1:1080". Empty = direct.
    proxy: str = ""
    system_prompt: str = DEFAULT_SYSTEM_PROMPT

    @property
    def models(self) -> list[str]:
        """Primary model followed by fallbacks, without duplicates."""
        return list(dict.fromkeys(m for m in (self.model, *self.fallback_models) if m))


def parse_model_list(text: str) -> tuple[str, ...]:
    return tuple(m.strip() for m in text.split(",") if m.strip())


class SettingsRepository:
    def __init__(self, db: Database):
        self._db = db

    def _read_all(self) -> dict[str, str]:
        with self._db.connect() as conn:
            return {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM settings")}

    def load(self) -> AppSettings:
        raw = self._read_all()
        defaults = AppSettings()
        return AppSettings(
            api_key=raw.get("api_key", ""),
            base_url=raw.get("base_url") or defaults.base_url,
            model=raw.get("model") or defaults.model,
            fallback_models=(
                parse_model_list(raw["fallback_models"]) if "fallback_models" in raw else defaults.fallback_models
            ),
            proxy=raw.get("proxy", ""),
            system_prompt=raw.get("system_prompt") or defaults.system_prompt,
        )

    def save(self, settings: AppSettings) -> None:
        values = {
            "api_key": settings.api_key,
            "base_url": settings.base_url,
            "model": settings.model,
            "fallback_models": ",".join(settings.fallback_models),
            "proxy": settings.proxy,
            # Store an unchanged default as empty so future default improvements still apply.
            "system_prompt": (
                "" if settings.system_prompt.strip() == DEFAULT_SYSTEM_PROMPT.strip() else settings.system_prompt
            ),
        }
        with self._db.connect() as conn:
            conn.executemany(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                values.items(),
            )
