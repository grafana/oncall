from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.utils.html import strip_tags

from apps.base.messaging import BaseMessagingBackend
from apps.base.utils import live_settings
from apps.email.alert_rendering import build_subject_and_title


class EmailBackend(BaseMessagingBackend):
    backend_id = "EMAIL"
    label = "Email"
    short_label = "Email"
    available_for_use = True
    templater = "apps.email.alert_rendering.AlertEmailTemplater"

    def serialize_user(self, user):
        return {"email": user.email}

    def notify_user(self, user, alert_group, notification_policy):
        subject, html_message = build_subject_and_title(alert_group)

        message = strip_tags(html_message)
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user.email]

        # todo: add to live settings
        connection = get_connection(
            host=live_settings.EMAIL_HOST,
            port=live_settings.EMAIL_PORT,
            username=live_settings.EMAIL_HOST_USER,
            password=live_settings.EMAIL_HOST_PASSWORD,
            use_tls=live_settings.EMAIL_USE_TLS,
            fail_silently=False,
        )

        # send email through Django setup
        send_mail(subject, message, email_from, recipient_list, html_message=html_message, connection=connection)
