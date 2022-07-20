import re

from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater
from common.utils import escape_html, url_re


class AlertClassicMarkdownTemplater(AlertTemplater):
    RENDER_FOR = "web"

    def _render_for(self):
        return self.RENDER_FOR

    def _postformat(self, templated_alert):
        link_substitution = {}
        if templated_alert.title:
            templated_alert.title = escape_html(self._slack_format_for_web(templated_alert.title))
        if templated_alert.message:
            message = escape_html(self._slack_format_for_web(templated_alert.message))
            link_matches = re.findall(url_re, message)
            for idx, link in enumerate(link_matches):
                substitution = f"amixrsubstitutedlink{idx}"
                link_substitution[substitution] = link
                message = message.replace(link, substitution)

        return templated_alert

    def _slack_format_for_web(self, data):
        sf = self.slack_formatter
        sf.hyperlink_mention_format = "[{title}]({url})"
        return sf.format(data)
