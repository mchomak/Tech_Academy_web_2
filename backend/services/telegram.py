import os
import logging

import httpx

logger = logging.getLogger(__name__)

TG_API = "https://api.telegram.org"


async def send_telegram_notification(text: str) -> None:
    token = os.getenv("TG_BOT_TOKEN", "")
    chat_id = os.getenv("TG_CHAT_ID", "")

    if not token or not chat_id:
        logger.warning("TG_BOT_TOKEN or TG_CHAT_ID not set — skipping notification")
        return

    url = f"{TG_API}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=payload)

    if resp.status_code != 200:
        logger.error("Telegram API error %s: %s", resp.status_code, resp.text)
        raise RuntimeError(f"Telegram API returned {resp.status_code}")

    logger.info("Telegram notification sent to chat %s", chat_id)
