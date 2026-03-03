import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

AUTH_PASSWORD = os.getenv("TG_AUTH_PASSWORD", "TechRise2010306")
USERS_FILE = Path(os.getenv("TG_USERS_FILE", "data/authorized_users.json"))

# In-memory state
_authorized_users: set = set()
_awaiting_password: set = set()


def _load_users() -> None:
    global _authorized_users
    if USERS_FILE.exists():
        try:
            data = json.loads(USERS_FILE.read_text())
            _authorized_users = set(data)
            logger.info("Loaded %d authorized user(s)", len(_authorized_users))
        except Exception:
            _authorized_users = set()


def _save_users() -> None:
    try:
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        USERS_FILE.write_text(json.dumps(list(_authorized_users)))
    except Exception as exc:
        logger.error("Failed to save authorized users: %s", exc)


def get_authorized_users() -> set:
    return _authorized_users.copy()


def handle_update(update: dict) -> dict | None:
    """Process a Telegram update, return sendMessage payload or None."""
    message = update.get("message")
    if not message:
        return None

    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    if text == "/start":
        _awaiting_password.add(chat_id)
        return {
            "chat_id": chat_id,
            "text": "Добро пожаловать! Введите пароль для доступа к заявкам:",
        }

    if chat_id in _awaiting_password:
        _awaiting_password.discard(chat_id)
        if text == AUTH_PASSWORD:
            _authorized_users.add(chat_id)
            _save_users()
            return {
                "chat_id": chat_id,
                "text": "\u2705 Авторизация успешна! Вы будете получать уведомления о новых заявках.",
            }
        return {
            "chat_id": chat_id,
            "text": "\u274c Неверный пароль. Отправьте /start чтобы попробовать снова.",
        }

    if chat_id in _authorized_users:
        return {
            "chat_id": chat_id,
            "text": "Вы авторизованы. Заявки будут приходить автоматически.",
        }

    return {
        "chat_id": chat_id,
        "text": "Для доступа отправьте /start",
    }


# Load on import
_load_users()
