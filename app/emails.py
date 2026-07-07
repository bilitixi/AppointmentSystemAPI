import secrets

from django.conf import settings
from django.core.mail import send_mail


def generate_verification_token():
    return secrets.token_urlsafe(32)


def send_verification_email(user, patient):
    verification_link = f"{settings.FRONTEND_URL}/verify-email/{patient.email_verification_token}"

    send_mail(
        subject="Verify your email address",
        message=(
            f"Hi {patient.firstName},\n\n"
            f"Please verify your email address by clicking the link below:\n"
            f"{verification_link}\n\n"
            f"If you did not create this account, you can ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
