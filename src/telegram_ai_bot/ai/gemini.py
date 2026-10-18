"""Minimal client for the Gemini generateContent REST API."""

import logging

import requests

from telegram_ai_bot import config
from telegram_ai_bot.ai.errors import AIError, AIErrorKind

log = logging.getLogger(__name__)


def classify_http_error(status: int, body: str) -> AIErrorKind:
    lowered = body.lower()
    if status == 403 and "<html" in lowered:
        # Google serves an HTML 403 page (not JSON) to blocked regions.
        return AIErrorKind.REGION_BLOCKED
    if status == 401 or "api_key_invalid" in lowered or (status == 400 and "api key" in lowered):
        return AIErrorKind.INVALID_API_KEY
    if status == 403:
        return AIErrorKind.PERMISSION_DENIED
    if status == 404:
        return AIErrorKind.MODEL_NOT_FOUND
    if status == 429:
        return AIErrorKind.RATE_LIMITED
    if status >= 500:
        return AIErrorKind.SERVER_ERROR
    return AIErrorKind.UNKNOWN


def proxies_for(proxy: str) -> dict[str, str] | None:
    if not proxy:
        return None  # requests still honours system / environment proxies
    if proxy.startswith("socks5://"):
        proxy = "socks5h://" + proxy.removeprefix("socks5://")  # resolve DNS through the proxy too
    return {"http": proxy, "https": proxy}


class GeminiClient:
    def __init__(self, api_key: str, base_url: str = config.GEMINI_BASE_URL, proxy: str = "",
                 session: requests.Session | None = None):
        if not api_key:
            raise AIError(AIErrorKind.MISSING_API_KEY)
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._proxies = proxies_for(proxy)
        self._session = session or requests.Session()

    def generate(self, model: str, system: str, contents: list[dict],
                 temperature: float = config.TEMPERATURE,
                 max_output_tokens: int = config.MAX_OUTPUT_TOKENS) -> str:
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_output_tokens},
        }
        try:
            resp = self._session.post(
                f"{self._base_url}/models/{model}:generateContent",
                json=body,
                headers={"x-goog-api-key": self._api_key},
                proxies=self._proxies,
                timeout=config.REQUEST_TIMEOUT_S,
            )
        except requests.RequestException as e:
            raise AIError(AIErrorKind.NETWORK_ERROR, str(e), model) from e

        if not resp.ok:
            kind = classify_http_error(resp.status_code, resp.text)
            try:
                detail = resp.json()["error"]["message"]
            except (ValueError, KeyError, TypeError):
                detail = f"HTTP {resp.status_code}"
            raise AIError(kind, detail, model)

        data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            reason = (data.get("promptFeedback") or {}).get("blockReason", "unknown")
            raise AIError(AIErrorKind.EMPTY_RESPONSE, f"no candidates (blockReason={reason})", model)
        parts = (candidates[0].get("content") or {}).get("parts") or []
        # Skip the model's "thought" parts; keep only the visible answer.
        text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
        if not text:
            reason = candidates[0].get("finishReason", "unknown")
            raise AIError(AIErrorKind.EMPTY_RESPONSE, f"empty text (finishReason={reason})", model)
        return text
