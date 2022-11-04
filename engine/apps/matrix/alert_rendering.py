from typing import Mapping

from django.template.loader import render_to_string
from emoji.core import emojize

from apps.alerts.incident_appearance.renderers.constants import DEFAULT_BACKUP_TITLE
from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater
from common.utils import convert_md_to_html, str_or_backup


class AlertMatrixTemplater(AlertTemplater):
    RENDER_FOR_MATRIX = "matrix"

    def _render_for(self):
        return self.RENDER_FOR_MATRIX


def build_raw_and_formatted_message(alert_group, user_id) -> Mapping[str, str]:
    alert = alert_group.alerts.first()
    templated_alert = AlertMatrixTemplater(alert).render()

    title_fallback = (
        f"#{alert_group.inside_organization_number} " f"{DEFAULT_BACKUP_TITLE} via {alert_group.channel.verbal_name}"
    )

    raw_message = templated_alert.message
    if raw_message:
        html_message = convert_md_to_html(templated_alert.message)
    else:
        html_message = None  # To avoid a NameError when passed to `str_or_backup` below

    content = render_to_string(
        "matrix_notification.html",
        {
            "url": alert_group.slack_permalink or alert_group.web_link,
            "title": str_or_backup(templated_alert.title, title_fallback),
            "message": str_or_backup(html_message, raw_message),
            "organization": alert_group.channel.organization.org_title,
            "integration": emojize(alert_group.channel.short_name, use_aliases=True),
        }
    )

    return {
        'raw': f"{user_id} {raw_message}",
        'formatted': f"{user_id} {content}"
    }
