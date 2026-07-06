from app.models import EmailTemplate

DEFAULT_TEMPLATES = {
    "register_verify": {
        "subject": "Verify your email address",
        "body": (
            "Hi {patient_firstName},\n\n"
            "Please verify your email address by clicking the link below:\n"
            "{verification_link}\n\n"
            "If you did not create this account, you can ignore this email."
        ),
    },
    "test_email": {
        "subject": "Test email",
        "body": "This is a test email sent to {to_email} to verify SMTP settings.",
    },
}


def get_template(template_type):
    template = EmailTemplate.objects.filter(template_type=template_type).first()

    if template:
        return template

    defaults = DEFAULT_TEMPLATES.get(template_type)

    if not defaults:
        return None

    return EmailTemplate.objects.create(
        template_type=template_type,
        subject=defaults["subject"],
        body=defaults["body"],
    )


def update_template(template_type, subject=None, body=None):
    template = get_template(template_type)

    if template is None:
        template = EmailTemplate.objects.create(
            template_type=template_type,
            subject=subject or "",
            body=body or "",
        )

    if subject is not None:
        template.subject = subject
    if body is not None:
        template.body = body

    template.save()
    return template
