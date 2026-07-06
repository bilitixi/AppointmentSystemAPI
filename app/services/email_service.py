from app.repositories.email_template import get_template
from app.repositories.notification_email import get_settings
from app.services.email_delivery import EmailDeliveryError, EmailDeliveryService
from app.services.template_render import render_template


class TemplateNotConfiguredError(Exception):
    pass


class NotificationEmailService:

    @staticmethod
    def send_templated(template_type, to_email, variables):
        settings_row = get_settings()

        if not settings_row.enabled:
            return

        template = get_template(template_type)

        if template is None:
            raise TemplateNotConfiguredError(
                f"No email template configured for '{template_type}'"
            )

        subject, body = render_template(template, variables)

        delivery = EmailDeliveryService(settings_row)
        delivery.send(to_email, subject, body)
