import pytest
import requests

from telegram_ai_bot.ai.errors import AIError, AIErrorKind
from telegram_ai_bot.ai.gemini import GeminiClient, classify_http_error, proxies_for


@pytest.mark.parametrize(("status", "body", "kind"), [
    (403, "<html><title>Error 403 (Forbidden)</title></html>", AIErrorKind.REGION_BLOCKED),
    (400, '{"error": {"message": "API key not valid", "status": "INVALID_ARGUMENT"}}', AIErrorKind.INVALID_API_KEY),
    (401, "{}", AIErrorKind.INVALID_API_KEY),
    (403, '{"error": {"message": "permission denied"}}', AIErrorKind.PERMISSION_DENIED),
    (404, "{}", AIErrorKind.MODEL_NOT_FOUND),
    (429, "{}", AIErrorKind.RATE_LIMITED),
    (503, "{}", AIErrorKind.SERVER_ERROR),
    (400, '{"error": {"message": "bad request"}}', AIErrorKind.UNKNOWN),
])
def test_classify_http_error(status, body, kind):
    assert classify_http_error(status, body) is kind


def test_proxies_for():
    assert proxies_for("") is None
    assert proxies_for("socks5://127.0.0.1:1080") == {
        "http": "socks5h://127.0.0.1:1080", "https": "socks5h://127.0.0.1:1080"}
    assert proxies_for("http://p:8080") == {"http": "http://p:8080", "https": "http://p:8080"}


class FakeResponse:
    def __init__(self, status=200, payload=None, text=""):
        self.status_code = status
        self.ok = status < 400
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("not json")
        return self._payload


class FakeSession:
    def __init__(self, response=None, exc=None):
        self.response, self.exc, self.requests = response, exc, []

    def post(self, url, **kwargs):
        self.requests.append((url, kwargs))
        if self.exc:
            raise self.exc
        return self.response


def client(session):
    return GeminiClient("KEY", "https://api.example/v1beta/", proxy="", session=session)


def test_generate_sends_request_and_skips_thoughts():
    session = FakeSession(FakeResponse(payload={"candidates": [{"content": {"parts": [
        {"text": "thinking…", "thought": True}, {"text": " Hello! "}]}}]}))
    text = client(session).generate("m1", "SYS", [{"role": "user", "parts": [{"text": "hi"}]}])
    assert text == "Hello!"
    url, kwargs = session.requests[0]
    assert url == "https://api.example/v1beta/models/m1:generateContent"
    assert kwargs["headers"] == {"x-goog-api-key": "KEY"}
    assert kwargs["json"]["systemInstruction"] == {"parts": [{"text": "SYS"}]}


def test_region_block_page_is_detected():
    session = FakeSession(FakeResponse(403, payload=None, text="<html>That’s an error.</html>"))
    with pytest.raises(AIError) as excinfo:
        client(session).generate("m1", "", [])
    assert excinfo.value.kind is AIErrorKind.REGION_BLOCKED
    assert excinfo.value.model == "m1"


def test_network_error():
    with pytest.raises(AIError) as excinfo:
        client(FakeSession(exc=requests.ConnectionError("down"))).generate("m1", "", [])
    assert excinfo.value.kind is AIErrorKind.NETWORK_ERROR


def test_blocked_prompt_is_empty_response():
    session = FakeSession(FakeResponse(payload={"promptFeedback": {"blockReason": "SAFETY"}}))
    with pytest.raises(AIError) as excinfo:
        client(session).generate("m1", "", [])
    assert excinfo.value.kind is AIErrorKind.EMPTY_RESPONSE
    assert "SAFETY" in excinfo.value.detail


def test_missing_api_key():
    with pytest.raises(AIError) as excinfo:
        GeminiClient("")
    assert excinfo.value.kind is AIErrorKind.MISSING_API_KEY
