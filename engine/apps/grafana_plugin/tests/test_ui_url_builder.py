import pytest

from apps.grafana_plugin.ui_url_builder import UIURLBuilder
from common.constants.plugin_ids import PluginID

GRAFANA_URL = "http://example.com"
ALERT_GROUP_ID = "1234"
INTEGRATION_ID = "5678"
SCHEDULE_ID = "lasdfasdf"


@pytest.fixture
def org_setup(make_organization):
    def _org_setup(is_grafana_irm_enabled = False):
        return make_organization(grafana_url=GRAFANA_URL, is_grafana_irm_enabled=is_grafana_irm_enabled)
    return _org_setup


@pytest.mark.parametrize(
    "page,call_kwargs,expected_url",
    [
        # oncall pages
        (
            UIURLBuilder.OnCallPage.HOME,
            {},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/",
        ),
        (
            UIURLBuilder.OnCallPage.ALERT_GROUPS,
            {},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/alert-groups",
        ),
        (
            UIURLBuilder.OnCallPage.ALERT_GROUP_DETAIL,
            {"id": ALERT_GROUP_ID, "path_extra": "/extra?foo=bar"},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/alert-groups/{ALERT_GROUP_ID}/extra?foo=bar",
        ),
        (
            UIURLBuilder.OnCallPage.INTEGRATION_DETAIL,
            {"id": INTEGRATION_ID},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/integrations/{INTEGRATION_ID}",
        ),
        (
            UIURLBuilder.OnCallPage.SCHEDULES,
            {},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/schedules",
        ),
        (
            UIURLBuilder.OnCallPage.SCHEDULE_DETAIL,
            {"id": SCHEDULE_ID},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/schedules/{SCHEDULE_ID}",
        ),
        (
            UIURLBuilder.OnCallPage.USERS,
            {},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/users",
        ),
        (
            UIURLBuilder.OnCallPage.USER_PROFILE,
            {},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/users/me",
        ),
        (
            UIURLBuilder.OnCallPage.CHATOPS,
            {},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/chat-ops",
        ),
        (
            UIURLBuilder.OnCallPage.SETTINGS,
            {},
            f"{GRAFANA_URL}/a/{PluginID.ONCALL}/settings",
        ),

        # incident pages
        (
            UIURLBuilder.IncidentPage.DECLARE_INCIDENT,
            {"path_extra": "?caption=abcd&url=asdf&title=test1234"},
            f"{GRAFANA_URL}/a/{PluginID.INCIDENT}/incidents/declare?caption=abcd&url=asdf&title=test1234",
        ),
    ],
)
@pytest.mark.django_db
def test_build_absolute_plugin_ui_url(org_setup, page, call_kwargs, expected_url):
    builder = UIURLBuilder(org_setup())
    assert builder.build_absolute_plugin_ui_url(page, **call_kwargs) == expected_url


@pytest.mark.django_db
def test_build_absolute_plugin_ui_url_overriden_base_url(org_setup):
    overriden_base_url = "http://overriden.com"
    builder = UIURLBuilder(org_setup(), base_url=overriden_base_url)
    url = builder.build_absolute_plugin_ui_url(UIURLBuilder.OnCallPage.CHATOPS)
    assert url == f"{overriden_base_url}/a/{PluginID.ONCALL}/chat-ops"


@pytest.mark.parametrize(
    "is_grafana_irm_enabled,expected_url",
    [
        (True, f"{GRAFANA_URL}/a/{PluginID.IRM}/alert-groups/{ALERT_GROUP_ID}"),
        (False, f"{GRAFANA_URL}/a/{PluginID.ONCALL}/alert-groups/{ALERT_GROUP_ID}"),
    ],
)
@pytest.mark.django_db
def test_build_absolute_plugin_ui_url_works_for_irm_and_oncall_plugins(org_setup, is_grafana_irm_enabled, expected_url):
    builder = UIURLBuilder(org_setup(is_grafana_irm_enabled))
    assert builder.build_absolute_plugin_ui_url(UIURLBuilder.OnCallPage.ALERT_GROUP_DETAIL, id=ALERT_GROUP_ID) == expected_url


@pytest.mark.django_db
def test_build_relative_plugin_ui_url(org_setup):
    builder = UIURLBuilder(org_setup())
    url = builder.build_relative_plugin_ui_url(UIURLBuilder.OnCallPage.ALERT_GROUP_DETAIL, id=ALERT_GROUP_ID)
    assert url == f"a/{PluginID.ONCALL}/alert-groups/1234"

