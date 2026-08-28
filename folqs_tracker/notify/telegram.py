"""Send the digest to Telegram via the Bot API.

Sent as plain text with no parse_mode: metric labels contain characters
(`&`, `$`, `(`, `-`) that Telegram's Markdown parser rejects, and a digest that
fails to send because of a dollar sign is worse than one without bold text.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.telegram.org/bot{token}/sendMessage"
LIMIT = 4096


def send_telegram(*, token: str, chat_id: str, text: str, timeout: int = 30) -> dict:
    if not token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must both be set")

    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text[:LIMIT],
        "disable_web_page_preview": "true",
    }).encode()

    request = urllib.request.Request(API.format(token=token), data=payload)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:300]
        # 400 here is almost always a chat_id the bot cannot reach: a user must
        # message the bot first, or it must be added to the group.
        raise RuntimeError(f"Telegram rejected the message ({exc.code}): {detail}") from exc
