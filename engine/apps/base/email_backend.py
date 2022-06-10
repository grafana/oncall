from django.conf import settings
from django.core.mail import send_mail

from apps.alerts.incident_appearance.templaters import AlertEmailTemplater
from apps.base.messaging import BaseMessagingBackend


class SimpleEmailBackend(BaseMessagingBackend):
    backend_id = "SMTPEMAIL"
    label = "Email"
    short_label = "Email"
    available_for_use = True

    def serialize_user(self, user):
        return {"email": user.email}

    def notify_user(self, user, alert_group, notification_policy):
        alert = alert_group.alerts.last()
        # use existing Email templater
        templated_alert = AlertEmailTemplater(alert).render()

        title = templated_alert.title
        message = templated_alert.message
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        # send email through Django setup
        send_mail(title, message, email_from, recipient_list)
