from django.template.loader import render_to_string
from emoji.core import emojize

from apps.alerts.incident_appearance.renderers.constants import DEFAULT_BACKUP_TITLE
from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater
from common.utils import convert_md_to_html, str_or_backup


class AlertEmailTemplater(AlertTemplater):
    RENDER_FOR_EMAIL = "email"

    def _render_for(self):
        return self.RENDER_FOR_EMAIL

    def _postformat(self, templated_alert):
        templated_alert.title = self._slack_format_for_email(templated_alert.title)
        templated_alert.message = self._slack_format_for_email(templated_alert.message)
        return templated_alert

    def _slack_format_for_email(self, data):
        sf = self.slack_formatter
        sf.hyperlink_mention_format = "{title} - {url}"
        return sf.format(data)


def build_subject_and_message(alert_group, emails_left):
    alert = alert_group.alerts.first()
    templated_alert = AlertEmailTemplater(alert).render()

    title_fallback = (
        f"#{alert_group.inside_organization_number} " f"{DEFAULT_BACKUP_TITLE} via {alert_group.channel.verbal_name}"
    )

    # default templates are the same as web templates, which are in Markdown format
    message = templated_alert.message
    if message:
        message = convert_md_to_html(templated_alert.message) if templated_alert.message else ""

    content = render_to_string(
        "email_notification.html",
        {
            "url": alert_group.slack_permalink or alert_group.web_link,
            "title": str_or_backup(templated_alert.title, title_fallback),
            "message": str_or_backup(message, ""),  # not render message at all if smth goes wrong
            "organization": alert_group.channel.organization.org_title,
            "integration": emojize(alert_group.channel.short_name, language="alias"),
            "limit_notification": emails_left <= 20,
            "emails_left": emails_left,
        },
    )

    title = str_or_backup(templated_alert.title, title_fallback)
    subject = f"[{title}] You are invited to check an alert group".replace("\n", "")

    return subject, content
