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

    def __init__(self, organization: "Organization", base_url: typing.Optional[str] = None) -> None:
        self.base_url = base_url if base_url else organization.grafana_url
        self.is_grafana_irm_enabled = organization.is_grafana_irm_enabled

    def build_url(self, page: typing.Union[OnCallPage, IncidentPage], path_extra: str = "", **kwargs) -> str:
        """
        Constructs an absolute URL to a Grafana plugin page.
        """

        if isinstance(page, self.IncidentPage):
            plugin_id = PluginID.INCIDENT
        else:
            plugin_id = PluginID.IRM if self.is_grafana_irm_enabled else PluginID.ONCALL

        return urljoin(self.base_url, f"a/{plugin_id}/{page.value.format(**kwargs)}{path_extra}")
