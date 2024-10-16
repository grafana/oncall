from apps.alerts.incident_appearance.renderers.base_renderer import AlertBaseRenderer, AlertGroupBaseRenderer
from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater
from apps.alerts.models import Alert, AlertGroup
from apps.mattermost.utils import MattermostEventAuthenticator
from common.api_helpers.utils import create_engine_url
from common.utils import is_string_with_visible_characters, str_or_backup


class MattermostMessageRenderer:
    def __init__(self, alert_group: AlertGroup):
        self.alert_group = alert_group

    def render_alert_group_message(self):
        attachments = AlertGroupMattermostRenderer(self.alert_group).render_alert_group_attachments()
        return {"props": {"attachments": attachments}}


class AlertMattermostTemplater(AlertTemplater):
    RENDER_FOR_MATTERMOST = "mattermost"

    def _render_for(self) -> str:
        return self.RENDER_FOR_MATTERMOST


class AlertMattermostRenderer(AlertBaseRenderer):
    def __init__(self, alert: Alert):
        super().__init__(alert)
        self.channel = alert.group.channel

    @property
    def templater_class(self):
        return AlertMattermostTemplater

    def render_alert_attachments(self):
        attachments = []
        title = str_or_backup(self.templated_alert.title, "Alert")
        message = ""
        if is_string_with_visible_characters(self.templated_alert.message):
            message = self.templated_alert.message
        attachments.append(
            {
                "fallback": "{}: {}".format(self.channel.get_integration_display(), self.alert.title),
                "title": title,
                "title_link": self.templated_alert.source_link,
                "text": message,
                "image_url": self.templated_alert.image_url,
            }
        )
        return attachments


class AlertGroupMattermostRenderer(AlertGroupBaseRenderer):
    def __init__(self, alert_group: AlertGroup):
        super().__init__(alert_group)

        self.alert_renderer = self.alert_renderer_class(self.alert_group.alerts.last())

    @property
    def alert_renderer_class(self):
        return AlertMattermostRenderer

    def render_alert_group_attachments(self):
        attachments = self.alert_renderer.render_alert_attachments()
        alert_group = self.alert_group

        if alert_group.resolved:
            attachments.append(
                {
                    "fallback": "Resolved...",
                    "text": alert_group.get_resolve_text(),
                }
            )
        elif alert_group.acknowledged:
            attachments.append(
                {
                    "fallback": "Acknowledged...",
                    "text": alert_group.get_acknowledge_text(),
                }
            )

        # append buttons to the initial attachment
        attachments[0]["actions"] = self._get_buttons_attachments()

        return self._set_attachments_color(attachments)

    def _get_buttons_attachments(self):
        actions = []

        def _make_actions(id, name, token):
            return {
                "id": id,
                "name": name,
                "integration": {
                    "url": create_engine_url("api/internal/v1/mattermost/event/"),
                    "context": {
                        "action": id,
                        "token": token,
                    },
                },
            }

        token = MattermostEventAuthenticator.create_token(organization=self.alert_group.channel.organization)
        if not self.alert_group.resolved:
            if self.alert_group.acknowledged:
                actions.append(_make_actions("unacknowledge", "Unacknowledge", token))
            else:
                actions.append(_make_actions("acknowledge", "Acknowledge", token))

        if self.alert_group.resolved:
            actions.append(_make_actions("unresolve", "Unresolve", token))
        else:
            actions.append(_make_actions("resolve", "Resolve", token))

        return actions

    def _set_attachments_color(self, attachments):
        color = "#a30200"  # danger
        if self.alert_group.silenced:
            color = "#dddddd"  # slack-grey
        if self.alert_group.acknowledged:
            color = "#daa038"  # warning
        if self.alert_group.resolved:
            color = "#2eb886"  # good

        for attachment in attachments:
            attachment["color"] = color

        return attachments
