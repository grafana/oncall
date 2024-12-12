import gzip
import json
from dataclasses import asdict
from unittest.mock import call, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.grafana_plugin.serializers.sync_data import SyncOnCallSettingsSerializer, SyncTeamSerializer
from apps.grafana_plugin.sync_data import SyncData, SyncSettings, SyncUser
from apps.grafana_plugin.tasks.sync_v2 import start_sync_organizations_v2, sync_organizations_v2
from common.constants.plugin_ids import PluginID


@pytest.mark.django_db
def test_auth_success(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    auth_headers = make_user_auth_headers(user, token)
    del auth_headers["HTTP_X-Grafana-Context"]

    with patch("apps.grafana_plugin.views.sync_v2.SyncV2View.do_sync", return_value=organization) as mock_sync:
        response = client.post(reverse("grafana-plugin:sync-v2"), format="json", **auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert mock_sync.called


@pytest.mark.django_db
def test_invalid_auth(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    organization, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    client = APIClient()

    auth_headers = make_user_auth_headers(user, "invalid-token")

    with patch("apps.grafana_plugin.views.sync_v2.SyncV2View.do_sync", return_value=organization) as mock_sync:
        response = client.post(reverse("grafana-plugin:sync-v2"), format="json", **auth_headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not mock_sync.called

    auth_headers = make_user_auth_headers(None, token, organization=organization)
    del auth_headers["HTTP_X-Instance-Context"]

    with patch("apps.grafana_plugin.views.sync_v2.SyncV2View.do_sync", return_value=organization) as mock_sync:
        response = client.post(reverse("grafana-plugin:sync-v2"), format="json", **auth_headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not mock_sync.called


@pytest.mark.parametrize(
    "api_token, sync_called",
    [
        ("", False),
        ("abc", False),
        ("glsa_abcdefghijklmnopqrstuvwxyz", True),
    ],
)
@pytest.mark.django_db
def test_skip_org_without_api_token(make_organization, api_token, sync_called):
    make_organization(api_token=api_token)

    with patch(
        "apps.grafana_plugin.helpers.GrafanaAPIClient.sync",
        return_value=(
            None,
            {
                "url": "",
                "connected": True,
                "status_code": status.HTTP_200_OK,
                "message": "",
            },
        ),
    ):
        with patch(
            "apps.grafana_plugin.tasks.sync_v2.sync_organizations_v2.apply_async", return_value=None
        ) as mock_sync:
            start_sync_organizations_v2()
            assert mock_sync.called == sync_called


@pytest.mark.parametrize("format", [("json"), ("gzip")])
@pytest.mark.django_db
def test_sync_v2_content_encoding(
    make_organization_and_user_with_plugin_token, make_user_auth_headers, settings, format
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    settings.LICENSE = settings.CLOUD_LICENSE_NAME
    client = APIClient()
    headers = make_user_auth_headers(None, token, organization=organization)

    data = SyncData(
        users=[
            SyncUser(
                id=user.user_id,
                name=user.username,
                login=user.username,
                email=user.email,
                role="Admin",
                avatar_url="",
                permissions=[],
                teams=[],
            )
        ],
        teams=[],
        team_members={},
        settings=SyncSettings(
            stack_id=organization.stack_id,
            org_id=organization.org_id,
            license=settings.CLOUD_LICENSE_NAME,
            oncall_api_url="http://localhost",
            oncall_token="",
            grafana_url="http://localhost",
            grafana_token="fake_token",
            rbac_enabled=False,
            incident_enabled=False,
            incident_backend_url="",
            labels_enabled=False,
            irm_enabled=False,
        ),
    )

    payload = asdict(data)
    headers["HTTP_Content-Type"] = "application/json"
    url = reverse("grafana-plugin:sync-v2")
    with patch("apps.grafana_plugin.views.sync_v2.apply_sync_data") as mock_sync:
        if format == "gzip":
            headers["HTTP_Content-Encoding"] = "gzip"
            json_data = json.dumps(payload)
            payload = gzip.compress(json_data.encode("utf-8"))
            response = client.generic("POST", url, data=payload, **headers)
        else:
            response = client.post(url, format=format, data=payload, **headers)

        assert response.status_code == status.HTTP_200_OK
        mock_sync.assert_called()


@patch("apps.grafana_plugin.helpers.client.GrafanaAPIClient.check_token", return_value=(None, {"connected": True}))
@pytest.mark.parametrize(
    "irm_enabled,expected",
    [
        (True, True),
        (False, False),
    ],
)
@pytest.mark.django_db
def test_sync_v2_irm_enabled(
    # mock this out so that we're not making a real network call, the sync v2 endpoint ends up calling
    # user_management.sync._sync_organization which calls GrafanaApiClient.check_token
    _mock_grafana_api_client_check_token,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    settings,
    irm_enabled,
    expected,
):
    settings.LICENSE = settings.CLOUD_LICENSE_NAME
    organization, _, token = make_organization_and_user_with_plugin_token()

    assert organization.is_grafana_irm_enabled is False

    client = APIClient()
    headers = make_user_auth_headers(None, token, organization=organization)
    url = reverse("grafana-plugin:sync-v2")

    data = SyncData(
        users=[],
        teams=[],
        team_members={},
        settings=SyncSettings(
            stack_id=organization.stack_id,
            org_id=organization.org_id,
            license=settings.CLOUD_LICENSE_NAME,
            oncall_api_url="http://localhost",
            oncall_token="",
            grafana_url="http://localhost",
            grafana_token="fake_token",
            rbac_enabled=False,
            incident_enabled=False,
            incident_backend_url="",
            labels_enabled=False,
            irm_enabled=irm_enabled,
        ),
    )

    response = client.post(url, format="json", data=asdict(data), **headers)
    assert response.status_code == status.HTTP_200_OK

    organization.refresh_from_db()
    assert organization.is_grafana_irm_enabled == expected


@patch("apps.grafana_plugin.helpers.client.GrafanaAPIClient.check_token", return_value=(None, {"connected": True}))
@pytest.mark.django_db
def test_sync_v2_none_values(
    # mock this out so that we're not making a real network call, the sync v2 endpoint ends up calling
    # user_management.sync._sync_organization which calls GrafanaApiClient.check_token
    _mock_grafana_api_client_check_token,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    settings,
):
    settings.LICENSE = settings.CLOUD_LICENSE_NAME
    organization, _, token = make_organization_and_user_with_plugin_token()

    client = APIClient()
    headers = make_user_auth_headers(None, token, organization=organization)
    url = reverse("grafana-plugin:sync-v2")

    data = SyncData(
        users=None,
        teams=None,
        team_members={},
        settings=SyncSettings(
            stack_id=organization.stack_id,
            org_id=organization.org_id,
            license=settings.CLOUD_LICENSE_NAME,
            oncall_api_url="http://localhost",
            oncall_token="",
            grafana_url="http://localhost",
            grafana_token="fake_token",
            rbac_enabled=False,
            incident_enabled=False,
            incident_backend_url="",
            labels_enabled=False,
            irm_enabled=False,
        ),
    )

    response = client.post(url, format="json", data=asdict(data), **headers)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "test_team, validation_pass",
    [
        ({"team_id": 1, "name": "Test Team", "email": "", "avatar_url": ""}, True),
        ({"team_id": 1, "name": "", "email": "", "avatar_url": ""}, False),
        ({"name": "ABC", "email": "", "avatar_url": ""}, False),
        ({"team_id": 1, "name": "ABC", "email": "test@example.com", "avatar_url": ""}, True),
        ({"team_id": 1, "name": "123", "email": "<invalid email>", "avatar_url": ""}, True),
    ],
)
@pytest.mark.django_db
def test_sync_team_serialization(test_team, validation_pass):
    serializer = SyncTeamSerializer(data=test_team)
    validation_error = None
    try:
        serializer.is_valid(raise_exception=True)
    except ValidationError as e:
        validation_error = e
    assert (validation_error is None) == validation_pass


@pytest.mark.django_db
def test_sync_grafana_url_serialization():
    data = {
        "stack_id": 123,
        "org_id": 321,
        "license": "OSS",
        "oncall_api_url": "http://localhost",
        "oncall_token": "",
        "grafana_url": "http://localhost/",
        "grafana_token": "fake_token",
        "rbac_enabled": False,
        "incident_enabled": False,
        "incident_backend_url": "",
        "labels_enabled": False,
        "irm_enabled": False,
    }
    serializer = SyncOnCallSettingsSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    cleaned_data = serializer.save()
    assert cleaned_data.grafana_url == "http://localhost"


@pytest.mark.django_db
def test_sync_batch_tasks(make_organization, settings):
    settings.SYNC_V2_MAX_TASKS = 2
    settings.SYNC_V2_PERIOD_SECONDS = 10
    settings.SYNC_V2_BATCH_SIZE = 2

    for _ in range(9):
        make_organization(api_token="glsa_abcdefghijklmnopqrstuvwxyz")

    expected_calls = [
        call(size=2, countdown=0),
        call(size=2, countdown=0),
        call(size=2, countdown=10),
        call(size=2, countdown=10),
        call(size=1, countdown=20),
    ]
    with patch("apps.grafana_plugin.tasks.sync_v2.sync_organizations_v2.apply_async", return_value=None) as mock_sync:
        start_sync_organizations_v2()

        def check_call(actual, expected):
            return (
                len(actual.args[0][0]) == expected.kwargs["size"]
                and actual.kwargs["countdown"] == expected.kwargs["countdown"]
            )

        for actual_call, expected_call in zip(mock_sync.call_args_list, expected_calls):
            assert check_call(actual_call, expected_call)

        assert mock_sync.call_count == len(expected_calls)


@patch(
    "apps.grafana_plugin.tasks.sync_v2.GrafanaAPIClient.api_post",
    return_value=(None, {"status_code": status.HTTP_200_OK}),
)
@pytest.mark.parametrize(
    "is_grafana_irm_enabled,expected",
    [
        (True, PluginID.IRM),
        (False, PluginID.ONCALL),
    ],
)
@pytest.mark.django_db
def test_sync_organizations_v2_calls_right_backend_plugin_sync_endpoint(
    mocked_grafana_api_client_api_post, make_organization, is_grafana_irm_enabled, expected
):
    org = make_organization(is_grafana_irm_enabled=is_grafana_irm_enabled)
    sync_organizations_v2(org_ids=[org.pk])
    mocked_grafana_api_client_api_post.assert_called_once_with(f"api/plugins/{expected}/resources/plugin/sync")
