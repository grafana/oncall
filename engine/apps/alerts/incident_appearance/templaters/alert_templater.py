from abc import ABC, abstractmethod
from dataclasses import dataclass

from django.conf import settings

from apps.base.messaging import get_messaging_backend_from_id
from apps.slack.slack_formatter import SlackFormatter
from common.jinja_templater import apply_jinja_template
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning


class TemplateLoader:
    def get_attr_template(self, attr, alert_receive_channel, render_for=None):
        """
        Trying to get attr template.
        First trying to get template for given combination of notification way and attr.
        If template is None - trying to get default template.
        If default template doesn't exist return None.
        """

        attr_name_for_template = self._get_attr_name_for_template(attr, alert_receive_channel, render_for)
        attr_template = getattr(alert_receive_channel, attr_name_for_template, None)
        if attr_template is None and render_for is not None:
            # check for additional messaging backend templates
            attr_template = alert_receive_channel.get_template_attribute(render_for, attr)
        return attr_template or self.get_default_attr_template(attr, alert_receive_channel, render_for)

    def get_default_attr_template(self, attr, alert_receive_channel, render_for=None):
        default_attr_template_dict = self._get_dict_of_default_templates(attr, alert_receive_channel, render_for)
        default_attr_template = default_attr_template_dict.get(alert_receive_channel.integration)
        if default_attr_template is None and render_for is not None:
            # check for additional messaging backend templates
            default_attr_template = alert_receive_channel.get_default_template_attribute(render_for, attr)
        return default_attr_template

    @staticmethod
    def _get_attr_name_for_template(attr, alert_receive_channel, render_for):
        """
        Get appropriate attribute name for template of alert receive channel
        First tries to get renderer specific attribute name, e.g. "slack_title_template"
        If it doesn't exist, fallbacks to common attribute name, e.g. "title_template"
        """
        if render_for is not None:
            renderer_specific_attr_name = f"{render_for}_{attr}_template"
            if hasattr(alert_receive_channel, renderer_specific_attr_name):
                return renderer_specific_attr_name

        return f"{attr}_template"

    @staticmethod
    def _get_dict_of_default_templates(attr, alert_receive_channel, render_for):
        """
        Get dict containing default templates for alert receive channel
        First tries to get renderer specific attribute name, e.g. "INTEGRATION_TO_DEFAULT_SLACK_TITLE_TEMPLATE"
        If it doesn't exist, fallbacks to common attribute name, e.g. "INTEGRATION_TO_DEFAULT_TITLE_TEMPLATE"
        """
        if render_for is not None:
            templates_dict_attr_name = f"INTEGRATION_TO_DEFAULT_{render_for.upper()}_{attr.upper()}_TEMPLATE"

            if hasattr(alert_receive_channel, templates_dict_attr_name):
                return getattr(alert_receive_channel, templates_dict_attr_name)

        return getattr(alert_receive_channel, f"INTEGRATION_TO_DEFAULT_{attr.upper()}_TEMPLATE", {})


@dataclass
class TemplatedAlert:
    title: str | None = None
    message: str | None = None
    image_url: str | None = None
    source_link: str | None = None


class AlertTemplater(ABC):
    def __init__(self, alert):
        self.alert = alert
        self.slack_formatter = SlackFormatter(alert.group.channel.organization)
        self.template_manager = TemplateLoader()
        self.alert_group_id = self.alert.group.inside_organization_number
        self.link = self.alert.group.web_link

    def render(self):
        """
        Rendering pipeline:
        1. preformatting - recursively traverses alert's raw request data and apply _preformat to string nodes
        2. applying templates - apply jinja templates to alert's raw request data
        3. postformatting - apply _postformat to the templated alert.
        :return:
        """
        if self._apply_preformatting():
            data = self._preformat_request_data(self.alert.raw_request_data)
        else:
            data = self.alert.raw_request_data
        templated_alert = self._apply_templates(data)
        templated_alert = self._postformat(templated_alert)
        return templated_alert

    def _apply_preformatting(self):
        """
        By default templater doesn't modify raw request data.
        If it is needed in concrete templater override this method.
        """
        return False

    def _preformat_request_data(self, request_data):
        if isinstance(request_data, dict):
            preformatted_data = {}
            for key in request_data.keys():
                preformatted_data[key] = self._preformat_request_data(request_data[key])
        elif isinstance(request_data, list):
            preformatted_data = []
            for value in request_data:
                preformatted_data.append(self._preformat_request_data(value))
        elif isinstance(request_data, str):
            preformatted_data = self._preformat(request_data)
        else:
            preformatted_data = request_data
        return preformatted_data

    def _preformat(self, data):
        return data

    def _postformat(self, templated_alert):
        return templated_alert

    def _apply_templates(self, data):
        channel = self.alert.group.channel

        # it's important that source_link comes before title,
        # since source_link is used to compute title
        attrs_to_render = ["source_link", "title", "message", "image_url"]

        templated_alert = TemplatedAlert()

        for attr in attrs_to_render:
            # determine is attr needs rendering by presence of appropriate template
            # for given combination of notification channel and attr.

            backend_id = self._render_for()
            message_backend = None
            if backend_id:
                message_backend = get_messaging_backend_from_id(backend_id.upper())

            need_rendering = (
                hasattr(channel, f"{self._render_for()}_{attr}_template")
                or hasattr(channel, f"{attr}_template")
                or message_backend is not None
            )

            if need_rendering:
                rendered_attr = self._render_attribute_with_template(
                    attr,
                    data,
                    channel,
                    templated_alert,
                )
                if rendered_attr == "None":
                    rendered_attr = None
                setattr(templated_alert, attr, rendered_attr)

        return templated_alert

    def _render_attribute_with_template(self, attr, data, channel, templated_alert: TemplatedAlert) -> str | None:
        """
        Get attr template and then apply it.
        If attr template is None or invalid will return None.
        """
        attr_template = self.template_manager.get_attr_template(attr, channel, self._render_for())
        if attr_template is not None:
            context = {
                "integration_name": channel.verbal_name,
                "source_link": templated_alert.source_link,
                "grafana_oncall_alert_group_id": self.alert_group_id,
                "grafana_oncall_incident_id": self.alert_group_id,  # Keep for backward compatibility
                "grafana_oncall_link": self.link,
            }
            # Hardcoding, as AlertWebTemplater.RENDER_FOR_WEB cause circular import
            render_for_web = "web"
            # Propagate rendered web templates to the other templates
            added_context = {}
            if self._render_for() != render_for_web:
                for attr in ["title", "message", "image_url"]:
                    added_attr_template = self.template_manager.get_attr_template(attr, channel, render_for_web)
                    if added_attr_template is not None:
                        result_length_limit = (
                            settings.JINJA_RESULT_TITLE_MAX_LENGTH
                            if attr == "title"
                            else settings.JINJA_RESULT_MAX_LENGTH
                        )
                        try:
                            added_context[f"web_{attr}"] = apply_jinja_template(
                                added_attr_template, data, result_length_limit=result_length_limit, **context
                            )
                        except (JinjaTemplateError, JinjaTemplateWarning) as e:
                            added_context[f"web_{attr}"] = e.fallback_message
                    else:
                        added_context[f"web_{attr}"] = f"web_{attr} is not set"
                context = {**context, **added_context}

            try:
                if attr == "title":
                    return apply_jinja_template(
                        attr_template, data, result_length_limit=settings.JINJA_RESULT_TITLE_MAX_LENGTH, **context
                    )
                else:
                    return apply_jinja_template(attr_template, data, **context)
            except (JinjaTemplateError, JinjaTemplateWarning) as e:
                return e.fallback_message

        return None

    @abstractmethod
    def _render_for(self) -> str:
        raise NotImplementedError
