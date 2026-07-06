from app.models import NotificationEmailSettings
from app.utils.secret_box import decrypt_secret, encrypt_secret

_SETTINGS_ID = 1


def get_settings():
    settings_row, _ = NotificationEmailSettings.objects.get_or_create(pk=_SETTINGS_ID)
    return settings_row


def get_decrypted_password(settings_row):
    return decrypt_secret(settings_row.smtp_password_encrypted)


def update_settings(data):
    settings_row = get_settings()

    password = data.pop("smtp_password", None)

    for field, value in data.items():
        setattr(settings_row, field, value)

    if password:
        settings_row.smtp_password_encrypted = encrypt_secret(password)

    settings_row.save()
    return settings_row
