import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@techrise.ru")

MAX_ATTEMPTS = 3
RETRY_DELAYS = [10, 30]


def send_email_notification(subject: str, body: str, to_email: str = "info@techrise.ru") -> None:
    """Send email with retry logic."""
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD]):
        logger.warning("SMTP configuration incomplete — skipping email")
        return

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = SMTP_FROM
            msg["To"] = to_email

            msg.attach(MIMEText(body, "html"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)

            logger.info("Email sent to %s (attempt %d)", to_email, attempt)
            return

        except smtplib.SMTPAuthenticationError as exc:
            logger.error("SMTP authentication failed — not retrying: %s", exc)
            return
        except smtplib.SMTPException as exc:
            logger.warning("SMTP error (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, exc)
        except Exception as exc:
            logger.warning("Email error (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, exc)

        if attempt < MAX_ATTEMPTS:
            import time

            delay = RETRY_DELAYS[attempt - 1]
            logger.info("Retrying email in %ds...", delay)
            time.sleep(delay)

    logger.error("Email to %s failed after %d attempts", to_email, MAX_ATTEMPTS)
