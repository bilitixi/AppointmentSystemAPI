import secrets

from django.conf import settings

from app.services.email_service import NotificationEmailService


def generate_verification_token():
    return secrets.token_urlsafe(32)


def send_verification_email(user, patient):
    verification_link = f"{settings.FRONTEND_URL}/verify-email/{patient.email_verification_token}"

    NotificationEmailService.send_templated(
        "register_verify",
        user.email,
        {
            "patient_firstName": patient.firstName,
            "verification_link": verification_link,
        },
    )
