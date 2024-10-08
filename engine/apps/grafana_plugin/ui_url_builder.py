import enum
import typing
from urllib.parse import urljoin

from common.constants.plugin_ids import PluginID

if typing.TYPE_CHECKING:
    from apps.user_management.models import Organization


class UIURLBuilder:
    """
    If `base_url` is passed into the constructor, it will override using `organization.grafana_url`
    """

    class OnCallPage(enum.StrEnum):
        HOME = ""

        ALERT_GROUPS = "alert-groups"
        ALERT_GROUP_DETAIL = "alert-groups/{id}"

        INTEGRATION_DETAIL = "integrations/{id}"

        SCHEDULES = "schedules"
        SCHEDULE_DETAIL = "schedules/{id}"

        USERS = "users"
        USER_PROFILE = "users/me"

        CHATOPS = "chat-ops"
        SETTINGS = "settings"

    class IncidentPage(enum.StrEnum):
        DECLARE_INCIDENT = "incidents/declare"

    PageType = typing.Union[OnCallPage, IncidentPage]

    def __init__(self, organization: "Organization", base_url: typing.Optional[str] = None) -> None:
        self.base_url = base_url if base_url else organization.grafana_url
        self.is_grafana_irm_enabled = organization.is_grafana_irm_enabled

    @property
    def active_plugin_ui_id(self) -> str:
        return PluginID.IRM if self.is_grafana_irm_enabled else PluginID.ONCALL

    def build_relative_plugin_ui_url(self, page: PageType, path_extra: str = "", **kwargs) -> str:
        if isinstance(page, self.IncidentPage):
            plugin_id = PluginID.INCIDENT
        else:
            plugin_id = self.active_plugin_ui_id

        return f"a/{plugin_id}/{page.value.format(**kwargs)}{path_extra}"

    def build_absolute_plugin_ui_url(self, page: PageType, path_extra: str = "", **kwargs) -> str:
        return urljoin(self.base_url, self.build_relative_plugin_ui_url(page, path_extra, **kwargs))
