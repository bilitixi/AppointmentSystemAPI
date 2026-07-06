import asyncio
from email.message import EmailMessage

import aiosmtplib

from app.repositories.notification_email import get_decrypted_password


class EmailDeliveryError(Exception):
    pass


class EmailDeliveryService:

    def __init__(self, settings_row):
        self.settings_row = settings_row

    def send(self, to_email, subject, body):
        return asyncio.run(self._send_async(to_email, subject, body))

    async def _send_async(self, to_email, subject, body):
        settings_row = self.settings_row

        message = EmailMessage()
        message["From"] = (
            f"{settings_row.from_name} <{settings_row.from_email}>"
            if settings_row.from_name
            else settings_row.from_email
        )
        message["To"] = to_email
        message["Subject"] = subject
        if settings_row.reply_to:
            message["Reply-To"] = settings_row.reply_to
        message.set_content(body)

        password = get_decrypted_password(settings_row)
        use_implicit_tls = settings_row.smtp_port == 465

        try:
            await aiosmtplib.send(
                message,
                hostname=settings_row.smtp_host,
                port=settings_row.smtp_port,
                username=settings_row.smtp_username or None,
                password=password or None,
                use_tls=use_implicit_tls,
                start_tls=None if use_implicit_tls else settings_row.smtp_use_tls,
            )
        except aiosmtplib.errors.SMTPAuthenticationError as exc:
            raise EmailDeliveryError(
                "SMTP authentication failed. If using Gmail, make sure you are using "
                "an App Password (not your regular account password) and that "
                "2-Step Verification is enabled."
            ) from exc
        except aiosmtplib.errors.SMTPException as exc:
            raise EmailDeliveryError(f"Failed to send email: {exc}") from exc
        except OSError as exc:
            raise EmailDeliveryError(
                f"Could not connect to SMTP server {settings_row.smtp_host}:{settings_row.smtp_port} ({exc})"
            ) from exc
