import typing
from urllib.parse import urljoin

from common.constants.plugin_ids import PluginID

if typing.TYPE_CHECKING:
    from apps.user_management.models import Organization


class UIURLBuilder:
    """
    If `base_url` is passed into the constructor, it will override using `organization.grafana_url`
    """

    def __init__(self, organization: "Organization", base_url: typing.Optional[str] = None) -> None:
        self.base_url = base_url if base_url else organization.grafana_url
        self.is_grafana_irm_enabled = organization.is_grafana_irm_enabled

    def _build_url(self, page: str, path_extra: str = "", plugin_id: typing.Optional[str] = None) -> str:
        """
        Constructs an absolute URL to a Grafana plugin page.
        """
        if not plugin_id:
            plugin_id = PluginID.IRM if self.is_grafana_irm_enabled else PluginID.ONCALL
        return urljoin(self.base_url, f"a/{plugin_id}/{page}{path_extra}")

    def home(self, path_extra: str = "") -> str:
        return self._build_url("", path_extra)

    def alert_groups(self, path_extra: str = "") -> str:
        return self._build_url("alert-groups", path_extra)

    def alert_group_detail(self, id: str, path_extra: str = "") -> str:
        return self._build_url(f"alert-groups/{id}", path_extra)

    def integration_detail(self, id: str, path_extra: str = "") -> str:
        return self._build_url(f"integrations/{id}", path_extra)

    def schedules(self, path_extra: str = "") -> str:
        return self._build_url("schedules", path_extra)

    def schedule_detail(self, id: str, path_extra: str = "") -> str:
        return self._build_url(f"schedules/{id}", path_extra)

    def users(self, path_extra: str = "") -> str:
        return self._build_url("users", path_extra)

    def user_profile(self, path_extra: str = "") -> str:
        return self._build_url("users/me", path_extra)

    def chatops(self, path_extra: str = "") -> str:
        return self._build_url("chat-ops", path_extra)

    def settings(self, path_extra: str = "") -> str:
        return self._build_url("settings", path_extra)

    def declare_incident(self, path_extra: str = "") -> str:
        return self._build_url("incidents/declare", path_extra, plugin_id=PluginID.INCIDENT)

    def service_page(self, service_name: str, path_extra: str = "") -> str:
        return self._build_url(f"service/{service_name}", path_extra, plugin_id=PluginID.SLO)
