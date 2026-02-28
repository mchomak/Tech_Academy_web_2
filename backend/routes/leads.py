import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from services.telegram import send_telegram_notification

logger = logging.getLogger(__name__)

router = APIRouter()


class LeadRequest(BaseModel):
    name: str
    phone: str
    telegram: str
    course: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Имя не может быть пустым")
        return v.strip()

    @field_validator("phone")
    @classmethod
    def phone_min_length(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 10:
            raise ValueError("Телефон должен содержать минимум 10 символов")
        return cleaned

    @field_validator("course")
    @classmethod
    def course_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Курс не может быть пустым")
        return v.strip()

    @field_validator("telegram")
    @classmethod
    def telegram_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("telegram не может быть пустым")
        return v.strip()


@router.post("/api/lead")
async def create_lead(lead: LeadRequest):
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    logger.info("New lead: %s / %s", lead.name, lead.course)

    text = (
        "\U0001f525 Новая заявка!\n"
        f"\U0001f464 Имя: {lead.name}\n"
        f"\U0001f4de Телефон: {lead.phone}\n"
        f"\U0001f4de Telegram: {lead.telegram}\n"
        f"\U0001f4da Курс: {lead.course}\n"
        f"\U0001f550 Время: {now}"
    )

    try:
        await send_telegram_notification(text)
    except Exception as exc:
        logger.error("Telegram notification failed: %s", exc)

    return {"status": "ok", "message": "Заявка принята"}
