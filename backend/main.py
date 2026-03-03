import os
import logging

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.leads import router as leads_router
from routes.bot import router as bot_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = FastAPI(title="academy API")

allowed_origins = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads_router)
app.include_router(bot_router)

logger = logging.getLogger(__name__)


@app.on_event("startup")
async def register_telegram_webhook():
    token = os.getenv("TG_BOT_TOKEN", "")
    webhook_url = os.getenv("TG_WEBHOOK_URL", "")
    if token and webhook_url:
        url = f"https://api.telegram.org/bot{token}/setWebhook"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json={"url": webhook_url})
            logger.info("Telegram webhook registration: %s", resp.text)
        except Exception as exc:
            logger.error("Failed to register Telegram webhook: %s", exc)
    else:
        logger.warning("TG_BOT_TOKEN or TG_WEBHOOK_URL not set — webhook not registered")


@app.get("/health")
async def health():
    return {"status": "ok"}
