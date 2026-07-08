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


def generate_password_reset_token():
    return secrets.token_urlsafe(32)


def send_password_reset_email(user, patient):
    reset_link = f"{settings.FRONTEND_URL}/reset-password/{patient.password_reset_token}"

    send_mail(
        subject="Reset your password",
        message=(
            f"Hi {patient.firstName},\n\n"
            f"We received a request to reset your password. Click the link below to choose a new one:\n"
            f"{reset_link}\n\n"
            f"This link will expire in 1 hour. If you did not request a password reset, you can ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
