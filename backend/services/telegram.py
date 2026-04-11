import asyncio
import os
import logging

import httpx

logger = logging.getLogger(__name__)

TG_API = "https://api.telegram.org"

MAX_ATTEMPTS = 3
# Задержки между попытками (секунды): 1→2: 10s, 2→3: 30s
RETRY_DELAYS = [10, 30]


async def _send_to_chat(token: str, chat_id: int, text: str) -> None:
    """Send a message to a single chat with retry logic."""
    url = f"{TG_API}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload)

            if resp.status_code == 200:
                logger.info("Telegram notification sent to %s (attempt %d)", chat_id, attempt)
                return

            if 400 <= resp.status_code < 500:
                logger.error(
                    "Telegram API client error %s for chat %s: %s — not retrying",
                    resp.status_code,
                    chat_id,
                    resp.text,
                )
                return

            logger.warning(
                "Telegram API server error %s for chat %s (attempt %d/%d)",
                resp.status_code,
                chat_id,
                attempt,
                MAX_ATTEMPTS,
            )

        except httpx.TimeoutException as exc:
            logger.warning("Telegram timeout for chat %s (attempt %d/%d): %s", chat_id, attempt, MAX_ATTEMPTS, exc)
        except httpx.ConnectError as exc:
            logger.warning("Telegram connect error for chat %s (attempt %d/%d): %s", chat_id, attempt, MAX_ATTEMPTS, exc)
        except Exception as exc:
            logger.warning("Telegram error for chat %s (attempt %d/%d): %s", chat_id, attempt, MAX_ATTEMPTS, exc)

        if attempt < MAX_ATTEMPTS:
            delay = RETRY_DELAYS[attempt - 1]
            logger.info("Retrying in %ds...", delay)
            await asyncio.sleep(delay)

    logger.error("Telegram notification to %s failed after %d attempts", chat_id, MAX_ATTEMPTS)


async def send_telegram_notification(text: str) -> None:
    from services.bot import get_authorized_users

    token = os.getenv("TG_BOT_TOKEN", "")
    if not token:
        logger.warning("TG_BOT_TOKEN not set — skipping notification")
        return

    chat_ids = get_authorized_users()

    # Фолбэк на TG_CHAT_ID если нет авторизованных пользователей
    fallback = os.getenv("TG_CHAT_ID", "")
    if not chat_ids and fallback:
        chat_ids = {int(cid.strip()) for cid in fallback.split(",") if cid.strip()}

    if not chat_ids:
        logger.warning("No authorized recipients — skipping notification")
        return

    for chat_id in chat_ids:
        await _send_to_chat(token, chat_id, text)
