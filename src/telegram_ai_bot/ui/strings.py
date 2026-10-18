"""All user-facing (Persian) text lives here, so the rest of the code stays language-neutral."""

from dataclasses import dataclass
from enum import Enum

from telegram_ai_bot.ai.errors import AIError, AIErrorKind
from telegram_ai_bot.telegram.events import BotEvent, BotStatus, EventType

APP_TITLE = "دستیار هوشمند تلگرام"
APP_SUBTITLE = "پاسخگویی خودکار با هوش مصنوعی"

# ----- Side panel -----
STATUS_LABELS = {
    BotStatus.OFF: "خاموش",
    BotStatus.LOADING: "در حال آماده‌سازی…",
    BotStatus.LISTENING: "در حال پاسخگویی",
    BotStatus.THINKING: "در حال نوشتن جواب…",
}
NO_CHAT_SELECTED = "هنوز چتی انتخاب نشده"
CHAT_LABEL = "چت: {name}"
STAT_REPLIES = "جواب ارسال‌شده"
STAT_KNOWLEDGE = "دانش فعال"
START = "▶  شروع پاسخگویی"
STOP = "⏸  توقف پاسخگویی"
REPLY_NOW = "💬  جواب همین الان"
REPLY_NOW_TIP = "یک بار، همین حالا با توجه به هیستوری چت جواب می‌دهد (حتی وقتی ربات خاموش است)"
RELOAD = "🔄  بارگذاری تلگرام"
RELOAD_TIP = "صفحه تلگرام را دوباره بارگذاری می‌کند"
SETTINGS_TIP = "تنظیمات"
REPLY_TO_PENDING = "هنگام شروع، به آخرین پیامِ بی‌جواب هم جواب بده"
TAB_ACTIVITY = "📋  فعالیت"
TAB_KNOWLEDGE = "📚  دانش"
TAB_KNOWLEDGE_COUNT = "📚  دانش ({count})"

# ----- Activity -----
ACTIVITY_EMPTY_TITLE = "هنوز فعالیتی نیست"
ACTIVITY_EMPTY_BODY = (
    "در سمت راست چت موردنظر را باز کنید و «شروع پاسخگویی» را بزنید.\n"
    "پیام‌ها و جواب‌ها اینجا نمایش داده می‌شوند."
)
CLEAR = "پاک کردن"
TYPING = "✍️ در حال نوشتن جواب"
INCOMING_LABEL = "📩 پیام دریافتی"
OUTGOING_LABEL = "🤖 جواب ربات"
MEDIA_MESSAGE = "[عکس / فایل]"
TECHNICAL_DETAILS = "جزئیات فنی"

# ----- Knowledge -----
KNOWLEDGE_SEARCH = "🔍  جستجو در دانش…"
KNOWLEDGE_ADD = "＋ افزودن"
KNOWLEDGE_HINT = "موارد فعال از پیام بعدی در جواب‌های ربات استفاده می‌شوند."
KNOWLEDGE_EMPTY_TITLE = "هنوز دانشی اضافه نکرده‌اید"
KNOWLEDGE_EMPTY_BODY = "با «＋ افزودن» اطلاعاتی مثل قیمت‌ها، ساعت کاری یا آدرس را وارد کنید تا ربات دقیق‌تر جواب دهد."
KNOWLEDGE_NO_RESULTS_TITLE = "چیزی پیدا نشد"
KNOWLEDGE_NO_RESULTS_BODY = "عبارت دیگری را جستجو کنید."
KNOWLEDGE_TOGGLE_TIP = "فعال / غیرفعال"
KNOWLEDGE_DIALOG_ADD = "افزودن دانش"
KNOWLEDGE_DIALOG_EDIT = "ویرایش دانش"
FIELD_TITLE = "عنوان"
FIELD_CONTENT = "متن"
TITLE_PLACEHOLDER = "مثلاً: ساعت کاری"
CONTENT_PLACEHOLDER = (
    "هر اطلاعاتی که ربات باید بداند، به زبان ساده.\n"
    "مثلاً: شنبه تا چهارشنبه از ۹ صبح تا ۶ عصر پاسخگو هستیم. پنجشنبه‌ها تا ۱ ظهر."
)
KNOWLEDGE_ENABLED = "فعال باشد (ربات در جواب‌ها از آن استفاده کند)"
INCOMPLETE_TITLE = "ناقص است"
INCOMPLETE_BODY = "لطفاً عنوان و متن را وارد کنید."
DELETE = "🗑 حذف"
DELETE_TITLE = "حذف"
DELETE_CONFIRM = "«{title}» حذف شود؟"
SAVE = "ذخیره"
CANCEL = "انصراف"

# ----- Settings -----
SETTINGS_TITLE = "تنظیمات"
SECTION_CONNECTION = "🔑 اتصال به Gemini"
FIELD_API_KEY = "کلید API"
API_KEY_PLACEHOLDER = "Paste your Gemini API key"
SHOW = "نمایش"
API_KEY_HINT = "کلید را رایگان از aistudio.google.com بگیرید."
TEST_CONNECTION = "🔌 تست اتصال"
TESTING = "در حال تست…"
TEST_OK = "اتصال برقرار است ✅"
TEST_PROMPT = "سلام! فقط برای تست اتصال: یک کلمه جواب بده."
SECTION_PROXY = "🌐 پروکسی"
PROXY_HINT = (
    "اگر تلگرام یا Gemini بدون فیلترشکن باز نمی‌شوند، آدرس پروکسی فیلترشکن خود را وارد کنید "
    "(socks5 یا http). خالی یعنی بدون پروکسی. "
    "تغییر پروکسی تلگرام بعد از بستن و باز کردن دوباره اپ اعمال می‌شود."
)
SECTION_PERSONA = "🧠 شخصیت و قوانین ربات"
PERSONA_HINT = "به ربات بگویید چطور رفتار کند: لحن، چه چیزهایی بگوید و چه چیزهایی نگوید."
RESET_PROMPT = "بازگشت به متن پیش‌فرض"
SECTION_ADVANCED = "⚙️ پیشرفته"
SHOW_ADVANCED = "نمایش تنظیمات پیشرفته ▾"
HIDE_ADVANCED = "پنهان کردن تنظیمات پیشرفته ▴"
FIELD_MODEL = "مدل اصلی"
FIELD_FALLBACKS = "مدل‌های جایگزین (اگر مدل اصلی خطا داد، به‌ترتیب امتحان می‌شوند؛ با کاما جدا کنید)"
FIELD_BASE_URL = "آدرس API"
PROXY_CHANGED_TITLE = "پروکسی تغییر کرد"
PROXY_CHANGED_BODY = "پروکسی Gemini از همین حالا اعمال می‌شود.\nبرای اعمال روی تلگرام، اپ را ببندید و دوباره باز کنید."

# ----- AI errors -----
AI_ERRORS: dict[AIErrorKind, tuple[str, str]] = {
    AIErrorKind.MISSING_API_KEY: (
        "کلید Gemini وارد نشده", "از دکمه ⚙️ تنظیمات، کلید Gemini را وارد و ذخیره کنید."),
    AIErrorKind.REGION_BLOCKED: (
        "دسترسی به Gemini مسدود است",
        "گوگل اتصال از ایران را قبول نمی‌کند. VPN را روشن کنید یا در تنظیمات پروکسی وارد کنید."),
    AIErrorKind.INVALID_API_KEY: (
        "کلید Gemini نامعتبر است", "کلید را در تنظیمات بررسی کنید یا از aistudio.google.com کلید جدید بگیرید."),
    AIErrorKind.PERMISSION_DENIED: (
        "اجازه دسترسی داده نشد", "کلید به این مدل دسترسی ندارد یا محدود شده است. کلید و مدل را بررسی کنید."),
    AIErrorKind.MODEL_NOT_FOUND: (
        "مدل پیدا نشد", "نام مدل در تنظیمات پیشرفته اشتباه است یا دیگر در دسترس نیست."),
    AIErrorKind.RATE_LIMITED: (
        "سقف استفاده پر شده", "تعداد درخواست‌ها زیاد بوده. چند دقیقه صبر کنید و بعد «جواب همین الان» را بزنید."),
    AIErrorKind.SERVER_ERROR: (
        "سرور Gemini موقتاً در دسترس نیست", "مشکل از سمت گوگل است. کمی بعد دوباره امتحان کنید."),
    AIErrorKind.NETWORK_ERROR: (
        "اتصال به اینترنت برقرار نشد", "اینترنت، VPN یا آدرس پروکسی را بررسی کنید."),
    AIErrorKind.EMPTY_RESPONSE: (
        "Gemini جوابی نداد", "ممکن است پیام به‌خاطر قوانین محتوایی گوگل رد شده باشد."),
    AIErrorKind.UNKNOWN: (
        "خطای غیرمنتظره", "جزئیات فنی را ببینید یا دوباره امتحان کنید."),
}


def ai_error_message(error: AIError) -> tuple[str, str]:
    return AI_ERRORS.get(error.kind, AI_ERRORS[AIErrorKind.UNKNOWN])


# ----- Bot events -----
class Tone(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARN = "warn"
    ERROR = "error"
    INCOMING = "in"
    OUTGOING = "out"


@dataclass(frozen=True, slots=True)
class EventText:
    tone: Tone
    title: str
    hint: str = ""
    detail: str = ""


def describe_event(event: BotEvent) -> EventText:
    match event.type:
        case EventType.STARTED:
            return EventText(Tone.INFO, f"ربات روی چت «{event.text}» فعال شد. در حال خواندن پیام‌های قبلی…")
        case EventType.HISTORY_LOADED:
            return EventText(Tone.SUCCESS, "آماده است",
                             f"{event.count} پیام قبلی خوانده شد. ربات منتظر پیام‌های جدید است.")
        case EventType.ANSWERING_PENDING:
            return EventText(Tone.INFO, "آخرین پیام بی‌جواب مانده بود؛ جوابش را می‌دهم.")
        case EventType.STOPPED:
            return EventText(Tone.INFO, "پاسخگویی متوقف شد.")
        case EventType.BUSY:
            return EventText(Tone.INFO, "ربات مشغول است؛ چند لحظه صبر کنید.")
        case EventType.NOT_LOGGED_IN:
            return EventText(Tone.WARN, "هنوز وارد تلگرام نشده‌اید",
                             "در سمت راست، QR را با تلگرام گوشی اسکن کنید (Settings ← Devices ← Link Desktop Device).")
        case EventType.NO_CHAT_OPEN:
            return EventText(Tone.WARN, "هیچ چتی باز نیست",
                             "در سمت راست روی چتی که می‌خواهید ربات جوابش را بدهد کلیک کنید، بعد دوباره امتحان کنید.")
        case EventType.CHAT_SWITCHED:
            return EventText(Tone.WARN, "چت عوض شد",
                             "ربات فقط روی چتی که با آن شروع شده کار می‌کند. به همان چت برگردید یا ربات را دوباره شروع کنید.")
        case EventType.CHAT_RESTORED:
            return EventText(Tone.INFO, "به چت برگشتید؛ پاسخگویی ادامه دارد.")
        case EventType.NO_MESSAGES:
            return EventText(Tone.WARN, "پیامی در این چت پیدا نشد", "ممکن است صفحه هنوز کامل لود نشده باشد.")
        case EventType.INCOMING:
            return EventText(Tone.INCOMING, event.text or MEDIA_MESSAGE)
        case EventType.OUTGOING:
            return EventText(Tone.OUTGOING, event.text)
        case EventType.NOTHING_TO_REPLY:
            return EventText(Tone.INFO, "جوابی لازم نبود (آخرین پیام از طرف خودتان است).")
        case EventType.AI_ERROR:
            title, hint = ai_error_message(event.error)
            return EventText(Tone.ERROR, title, hint, str(event.error))
        case EventType.PAGE_LOAD_FAILED:
            return EventText(Tone.WARN, "تلگرام باز نشد",
                             "اینترنت یا VPN را بررسی کنید. اگر از پروکسی استفاده می‌کنید، آن را در ⚙️ تنظیمات وارد کنید "
                             "و اپ را دوباره باز کنید. بعد «بارگذاری تلگرام» را بزنید.")
    return EventText(Tone.INFO, event.type.name)
