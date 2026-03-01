import asyncio
import os
import logging

import httpx

logger = logging.getLogger(__name__)

TG_API = "https://api.telegram.org"

MAX_ATTEMPTS = 3
# Задержки между попытками (секунды): 1→2: 10s, 2→3: 30s
RETRY_DELAYS = [10, 30]


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

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload)

            if resp.status_code == 200:
                logger.info("Telegram notification sent (attempt %d)", attempt)
                return

            # 4xx — ошибка конфигурации (неверный токен, chat_id), ретрай не поможет
            if 400 <= resp.status_code < 500:
                logger.error(
                    "Telegram API client error %s: %s — not retrying",
                    resp.status_code,
                    resp.text,
                )
                return

            logger.warning(
                "Telegram API server error %s (attempt %d/%d)",
                resp.status_code,
                attempt,
                MAX_ATTEMPTS,
            )

        except httpx.TimeoutException as exc:
            logger.warning("Telegram request timed out (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, exc)
        except httpx.ConnectError as exc:
            logger.warning("Telegram connection error (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, exc)
        except Exception as exc:
            logger.warning("Telegram unexpected error (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, exc)

        if attempt < MAX_ATTEMPTS:
            delay = RETRY_DELAYS[attempt - 1]
            logger.info("Retrying Telegram notification in %ds...", delay)
            await asyncio.sleep(delay)

    logger.error("Telegram notification failed after %d attempts", MAX_ATTEMPTS)