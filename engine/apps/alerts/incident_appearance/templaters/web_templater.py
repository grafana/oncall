import re

from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater
from common.utils import convert_md_to_html, escape_html, url_re, urlize_with_respect_to_a


class AlertWebTemplater(AlertTemplater):
    RENDER_FOR_WEB = "web"

    def _render_for(self):
        return self.RENDER_FOR_WEB

    def _postformat(self, templated_alert):
        link_substitution = {}
        if templated_alert.title:
            templated_alert.title = escape_html(self._slack_format_for_web(templated_alert.title))
        if templated_alert.message:
            message = escape_html(self._slack_format_for_web(templated_alert.message))
            link_matches = re.findall(url_re, message)
            for idx, link in enumerate(link_matches):
                substitution = f"oncallsubstitutedlink{idx}"
                link_substitution[substitution] = link
                message = message.replace(link, substitution)
            message = convert_md_to_html(message)
            for substitution, original_link in link_substitution.items():
                message = message.replace(substitution, original_link)
            templated_alert.message = urlize_with_respect_to_a(message)
        if templated_alert.image_url:
            templated_alert.image_url = escape_html(templated_alert.image_url)

        return templated_alert

    def _slack_format_for_web(self, data):
        sf = self.slack_formatter
        sf.hyperlink_mention_format = "[{title}]({url})"
        return sf.format(data)
