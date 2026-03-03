import os
import logging

import httpx
from fastapi import APIRouter, Request

from services.bot import handle_update

logger = logging.getLogger(__name__)

router = APIRouter()

TG_API = "https://api.telegram.org"


@router.post("/api/tg-webhook")
async def tg_webhook(request: Request):
    update = await request.json()
    response = handle_update(update)

    if response:
        token = os.getenv("TG_BOT_TOKEN", "")
        if token:
            url = f"{TG_API}/bot{token}/sendMessage"
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    await client.post(url, json=response)
            except Exception as exc:
                logger.error("Failed to send bot reply: %s", exc)

    return {"ok": True}
