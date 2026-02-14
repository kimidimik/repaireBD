import logging
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger("repairs")


def send_telegram_message(message: str, chat_id: Optional[str] = None) -> None:
    token = settings.TELEGRAM_BOT_TOKEN
    destination = chat_id or settings.TELEGRAM_CHAT_ID
    if not token or not destination:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": destination, "text": message}, timeout=5)
    except requests.RequestException as exc:
        logger.warning("Telegram notification failed: %s", exc)
