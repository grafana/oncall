import pytest

from apps.grafana_plugin.ui_url_builder import UIURLBuilder
from common.constants.plugin_ids import PluginID

GRAFANA_URL = "http://example.com"
ALERT_GROUP_ID = "1234"
INTEGRATION_ID = "5678"
SCHEDULE_ID = "lasdfasdf"
PATH_EXTRA = "/extra?foo=bar"


@pytest.fixture
def org_setup(make_organization):
    def _org_setup(is_grafana_irm_enabled=False):
        return make_organization(grafana_url=GRAFANA_URL, is_grafana_irm_enabled=is_grafana_irm_enabled)

    return _org_setup


@pytest.mark.parametrize(
    "func,call_kwargs,expected_url",
    [
        # oncall pages
        (
            "home",
            {"path_extra": PATH_EXTRA},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}{PATH_EXTRA}",
        ),
        (
            "alert_groups",
            {"path_extra": PATH_EXTRA},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/alert-groups{PATH_EXTRA}",
        ),
        (
            "alert_group_detail",
            {"id": ALERT_GROUP_ID, "path_extra": PATH_EXTRA},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/alert-groups/{ALERT_GROUP_ID}{PATH_EXTRA}",
        ),
        (
            "integration_detail",
            {"id": INTEGRATION_ID, "path_extra": PATH_EXTRA},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/integrations/{INTEGRATION_ID}{PATH_EXTRA}",
        ),
        (
            "schedules",
            {"path_extra": PATH_EXTRA},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/schedules{PATH_EXTRA}",
        ),
        (
            "schedule_detail",
            {"id": SCHEDULE_ID, "path_extra": PATH_EXTRA},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/schedules/{SCHEDULE_ID}{PATH_EXTRA}",
        ),
        (
            "users",
            {"path_extra": PATH_EXTRA},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/users{PATH_EXTRA}",
        ),
        (
            "user_profile",
            {"path_extra": PATH_EXTRA},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/users/me{PATH_EXTRA}",
        ),
        (
            "chatops",
            {"path_extra": PATH_EXTRA},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/chat-ops{PATH_EXTRA}",
        ),
        (
            "settings",
            {"path_extra": PATH_EXTRA},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/settings{PATH_EXTRA}",
        ),
        # incident pages
        (
            "declare_incident",
            {"path_extra": "?caption=abcd&url=asdf&title=test1234"},
            f"{GRAFANA_URL}/a/{PluginID.INCIDENT}/incidents/declare?caption=abcd&url=asdf&title=test1234",
        ),
    ],
)
@pytest.mark.django_db
def test_build_page_urls(org_setup, func, call_kwargs, expected_url):
    builder = UIURLBuilder(org_setup())
    assert getattr(builder, func)(**call_kwargs) == expected_url


@pytest.mark.django_db
def test_build_url_overriden_base_url(org_setup):
    overriden_base_url = "http://overriden.com"
    builder = UIURLBuilder(org_setup(), base_url=overriden_base_url)
    assert builder.chatops() == f"{overriden_base_url}/a/{PluginID.ONCALL}/chat-ops"


@pytest.mark.parametrize(
    "is_grafana_irm_enabled,expected_url",
    [
        (True, f"{GRAFANA_URL}/a/{PluginID.IRM}/alert-groups/{ALERT_GROUP_ID}"),
        (False, f"{GRAFANA_URL}/a/{PluginID.ONCALL}/alert-groups/{ALERT_GROUP_ID}"),
    ],
)
@pytest.mark.django_db
def test_build_url_works_for_irm_and_oncall_plugins(org_setup, is_grafana_irm_enabled, expected_url):
    assert UIURLBuilder(org_setup(is_grafana_irm_enabled)).alert_group_detail(ALERT_GROUP_ID) == expected_url


@pytest.mark.django_db
def test_build_url_service_detail_page(org_setup):
    builder = UIURLBuilder(org_setup())
    assert builder.service_page("service-a") == f"{GRAFANA_URL}/a/{PluginID.SLO}/service/service-a"
