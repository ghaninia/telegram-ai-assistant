"""Application constants. User-editable values live in storage.settings instead."""

TELEGRAM_URL = "https://web.telegram.org/k/"

# Telegram Web works best with a regular desktop Chrome user agent.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)

# --- Bot behaviour ---
POLL_INTERVAL_MS = 2_000
# Wait after a new message so several quick messages get a single reply.
DEBOUNCE_MS = 4_000
# How many times to scroll up on start to load older history.
HISTORY_SCROLLS = 5
HISTORY_SCROLL_WAIT_MS = 1_500
# Most recent messages sent to the model.
HISTORY_LIMIT = 100
REPLY_TO_PENDING_DEFAULT = True

# --- Gemini defaults (overridable from the settings dialog) ---
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = "gemini-3.1-flash-lite"
GEMINI_FALLBACK_MODELS = ("gemini-3-flash-preview", "gemini-3.5-flash-lite", "gemini-3.5-flash")
TEMPERATURE = 0.7
MAX_OUTPUT_TOKENS = 2_000
REQUEST_TIMEOUT_S = 60
