"""JavaScript run inside Telegram Web (K version).

If Telegram changes its markup, only the selectors below should need updating.
"""

import json

SEL_CHAT_LIST = "#column-left .chatlist"
SEL_CHAT_TITLE = "#column-center .chat-info .peer-title"
SEL_BUBBLES = "#column-center .bubbles-inner .bubble[data-mid]:not(.service)"
SEL_SCROLLABLE = "#column-center .bubbles .scrollable"
SEL_INPUT = "#column-center .input-message-input[contenteditable='true']"
SEL_SEND_BUTTON = "#column-center .btn-send"

# Elements inside a bubble that are not part of the message text.
_NON_TEXT = ".time, .time-inner, .reactions, .reply, .name, .bubble-name-first, .document-container, .web, .via"


def _iife(body: str) -> str:
    return f"(function(){{{body}}})()"


# Returns a JSON string (Qt WebEngine does not reliably convert JS objects/arrays):
# {loggedIn, chatId, title, history: [[messageId, "in"|"out", text], ...]}
STATE_SCRIPT = _iife(f"""
const history = [];
for (const bubble of document.querySelectorAll({json.dumps(SEL_BUBBLES)})) {{
  const direction = bubble.classList.contains('is-out') ? 'out' : 'in';
  let text = '';
  const message = bubble.querySelector('.message');
  if (message) {{
    const clone = message.cloneNode(true);
    clone.querySelectorAll({json.dumps(_NON_TEXT)}).forEach(e => e.remove());
    const translatable = clone.querySelector('.translatable-message');
    text = ((translatable || clone).innerText || '').trim();
  }}
  history.push([bubble.dataset.mid, direction, text]);
}}
const title = document.querySelector({json.dumps(SEL_CHAT_TITLE)});
return JSON.stringify({{
  loggedIn: !!document.querySelector({json.dumps(SEL_CHAT_LIST)}),
  chatId: location.hash || '',
  title: title ? title.innerText.trim() : '',
  history: history,
}});
""")


def scroll_script(to_top: bool) -> str:
    target = "0" if to_top else "el.scrollHeight"
    return _iife(f"const el = document.querySelector({json.dumps(SEL_SCROLLABLE)}); if (el) el.scrollTop = {target};")


def send_script(text: str) -> str:
    """Type text into the composer and send it.

    execCommand('insertText') is used instead of synthetic key events so Persian text and emoji work.
    """
    return _iife(f"""
const box = document.querySelector({json.dumps(SEL_INPUT)});
if (!box) return false;
box.focus();
document.execCommand('selectAll', false, null);
document.execCommand('delete', false, null);
document.execCommand('insertText', false, {json.dumps(text)});
box.dispatchEvent(new Event('input', {{bubbles: true}}));
setTimeout(() => {{
  const button = document.querySelector({json.dumps(SEL_SEND_BUTTON)});
  if (button) button.click();
  else box.dispatchEvent(new KeyboardEvent('keydown', {{key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true}}));
}}, 300);
return true;
""")
