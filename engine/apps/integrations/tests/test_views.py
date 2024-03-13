from unittest.mock import call, patch

import pytest
from django import test
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import OperationalError
from django.urls import reverse
from django.utils import timezone
from pytest_django.plugin import _DatabaseBlocker
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertReceiveChannel
from apps.integrations.mixins import AlertChannelDefiningMixin
from apps.integrations.views import UniversalAPIView

# https://github.com/pytest-dev/pytest-xdist/issues/432#issuecomment-528510433
INTEGRATION_TYPES = sorted(AlertReceiveChannel.INTEGRATION_TYPES)


class DatabaseBlocker(_DatabaseBlocker):
    """Customize pytest_django db blocker to raise OperationalError exception."""

    def _blocking_wrapper(*args, **kwargs):
        __tracebackhide__ = True
        __tracebackhide__  # Silence pyflakes
        # mimic DB unavailable error
        raise OperationalError("Database access disabled")


def setup_failing_redis_cache(settings):
    settings.DJANGO_REDIS_IGNORE_EXCEPTIONS = True
    settings.RATELIMIT_FAIL_OPEN = True
    settings.CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://no-redis-here/",
        }
    }


@patch("apps.integrations.views.create_alert")
@pytest.mark.parametrize(
    "integration_type",
    [
        arc_type
        for arc_type in INTEGRATION_TYPES
        if arc_type not in ["amazon_sns", "grafana", "alertmanager", "grafana_alerting", "maintenance"]
    ],
)
@pytest.mark.django_db
def test_integration_universal_endpoint(
    mock_create_alert, make_organization_and_user, make_alert_receive_channel, integration_type
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=integration_type,
    )

    client = APIClient()
    url = reverse(
        "integrations:universal",
        kwargs={"integration_type": integration_type, "alert_channel_key": alert_receive_channel.token},
    )

    data = {"foo": "bar"}
    now = timezone.now()
    with patch("django.utils.timezone.now") as mock_now:
        mock_now.return_value = now
        response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK

    mock_create_alert.apply_async.assert_called_once_with(
        [],
        {
            "title": None,
            "message": None,
            "image_url": None,
            "link_to_upstream_details": None,
            "alert_receive_channel_pk": alert_receive_channel.pk,
            "integration_unique_data": None,
            "raw_request_data": data,
            "received_at": now.isoformat(),
        },
    )


@patch("apps.integrations.views.create_alert")
@pytest.mark.parametrize(
    "integration_type",
    [
        arc_type
        for arc_type in INTEGRATION_TYPES
        if arc_type not in ["amazon_sns", "grafana", "alertmanager", "grafana_alerting", "maintenance"]
    ],
)
@pytest.mark.django_db
def test_integration_universal_endpoint_no_data(
    mock_create_alert, make_organization_and_user, make_alert_receive_channel, integration_type
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=integration_type,
    )

    url = reverse(
        "integrations:universal",
        kwargs={"integration_type": integration_type, "alert_channel_key": alert_receive_channel.token},
    )
    # django test client forces an empty data in the request, build from scratch instead
    factory = test.RequestFactory()
    req = factory.post(url)
    # mimic middlewares setting up metadata
    req.alert_receive_channel = alert_receive_channel
    req.data = None
    integration_view = UniversalAPIView()
    integration_view.request = req
    response = integration_view.post(req, integration_type=integration_type)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    mock_create_alert.apply_async.assert_not_called()


@patch("apps.integrations.views.create_alertmanager_alerts")
@pytest.mark.django_db
def test_integration_grafana_endpoint_wrong_endpoint(
    mock_create_alertmanager_alerts, make_organization_and_user, make_alert_receive_channel
):
    integration_type = "grafana_alerting"
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=integration_type,
    )

    client = APIClient()
    url = reverse("integrations:grafana", kwargs={"alert_channel_key": alert_receive_channel.token})

    response = client.post(url, {}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    mock_create_alertmanager_alerts.assert_not_called()


@patch("apps.integrations.views.create_alertmanager_alerts")
@pytest.mark.django_db
def test_integration_grafana_endpoint_has_alerts(
    mock_create_alertmanager_alerts, settings, make_organization_and_user, make_alert_receive_channel
):
    settings.DEBUG = False

    integration_type = "grafana"
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=integration_type,
    )

    client = APIClient()
    url = reverse("integrations:grafana", kwargs={"alert_channel_key": alert_receive_channel.token})

    data = {
        "alerts": [
            {
                "foo": 123,
            },
            {
                "foo": 456,
            },
        ]
    }
    now = timezone.now()
    with patch("django.utils.timezone.now") as mock_now:
        mock_now.return_value = now
        response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK

    mock_create_alertmanager_alerts.apply_async.assert_has_calls(
        [
            call((alert_receive_channel.pk, data["alerts"][0]), kwargs={"received_at": now.isoformat()}),
            call((alert_receive_channel.pk, data["alerts"][1]), kwargs={"received_at": now.isoformat()}),
        ]
    )


@patch("apps.integrations.views.create_alert")
@pytest.mark.django_db
def test_integration_old_grafana_endpoint(
    mock_create_alert, settings, make_organization_and_user, make_alert_receive_channel
):
    settings.DEBUG = False

    integration_type = "grafana"
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=integration_type,
    )

    client = APIClient()
    url = reverse("integrations:grafana", kwargs={"alert_channel_key": alert_receive_channel.token})

    data = {}
    now = timezone.now()
    with patch("django.utils.timezone.now") as mock_now:
        mock_now.return_value = now
        response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK

    mock_create_alert.apply_async.assert_called_once_with(
        [],
        {
            "title": "Title",
            "message": None,
            "image_url": None,
            "link_to_upstream_details": None,
            "alert_receive_channel_pk": alert_receive_channel.pk,
            "integration_unique_data": '{"evalMatches": []}',
            "raw_request_data": data,
            "received_at": now.isoformat(),
        },
    )


@patch("apps.integrations.views.create_alert")
@pytest.mark.parametrize(
    "integration_type",
    [
        arc_type
        for arc_type in INTEGRATION_TYPES
        if arc_type not in ["amazon_sns", "grafana", "alertmanager", "grafana_alerting", "maintenance"]
    ],
)
@pytest.mark.django_db
def test_integration_universal_endpoint_not_allow_files(
    mock_create_alert, make_organization_and_user, make_alert_receive_channel, integration_type
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=integration_type,
    )

    client = APIClient()
    url = reverse(
        "integrations:universal",
        kwargs={"integration_type": integration_type, "alert_channel_key": alert_receive_channel.token},
    )

    test_file = SimpleUploadedFile("testing", b"file_content")
    data = {"foo": "bar", "f": test_file}
    response = client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert not mock_create_alert.apply_async.called


@patch("apps.integrations.views.create_alert")
@pytest.mark.parametrize(
    "integration_type",
    [
        arc_type
        for arc_type in INTEGRATION_TYPES
        if arc_type not in ["amazon_sns", "grafana", "alertmanager", "grafana_alerting", "maintenance"]
    ],
)
@pytest.mark.django_db
def test_integration_universal_endpoint_works_without_db(
    mock_create_alert, make_organization_and_user, make_alert_receive_channel, integration_type
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=integration_type,
    )

    client = APIClient()
    url = reverse(
        "integrations:universal",
        kwargs={"integration_type": integration_type, "alert_channel_key": alert_receive_channel.token},
    )

    # populate cache
    AlertChannelDefiningMixin().update_alert_receive_channel_cache()

    now = timezone.now()
    with patch("django.utils.timezone.now") as mock_now:
        mock_now.return_value = now
        # disable DB access
        with DatabaseBlocker().block():
            data = {"foo": "bar"}
            response = client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK

    mock_create_alert.apply_async.assert_called_once_with(
        [],
        {
            "title": None,
            "message": None,
            "image_url": None,
            "link_to_upstream_details": None,
            "alert_receive_channel_pk": alert_receive_channel.pk,
            "integration_unique_data": None,
            "raw_request_data": data,
            "received_at": now.isoformat(),
        },
    )


@patch("apps.integrations.views.create_alertmanager_alerts")
@pytest.mark.django_db
def test_integration_grafana_endpoint_without_db_has_alerts(
    mock_create_alertmanager_alerts, settings, make_organization_and_user, make_alert_receive_channel
):
    settings.DEBUG = False

    integration_type = "grafana"
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=integration_type,
    )

    client = APIClient()
    url = reverse("integrations:grafana", kwargs={"alert_channel_key": alert_receive_channel.token})

    data = {
        "alerts": [
            {
                "foo": 123,
            },
            {
                "foo": 456,
            },
        ]
    }

    # populate cache
    AlertChannelDefiningMixin().update_alert_receive_channel_cache()

    now = timezone.now()
    with patch("django.utils.timezone.now") as mock_now:
        mock_now.return_value = now
        # disable DB access
        with DatabaseBlocker().block():
            response = client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK

    mock_create_alertmanager_alerts.apply_async.assert_has_calls(
        [
            call((alert_receive_channel.pk, data["alerts"][0]), kwargs={"received_at": now.isoformat()}),
            call((alert_receive_channel.pk, data["alerts"][1]), kwargs={"received_at": now.isoformat()}),
        ]
    )


@patch("apps.integrations.views.create_alert")
@pytest.mark.parametrize(
    "integration_type",
    [
        arc_type
        for arc_type in INTEGRATION_TYPES
        if arc_type not in ["amazon_sns", "grafana", "alertmanager", "grafana_alerting", "maintenance"]
    ],
)
@pytest.mark.django_db
def test_integration_universal_endpoint_works_without_cache(
    mock_create_alert,
    make_organization_and_user,
    make_alert_receive_channel,
    integration_type,
    settings,
):
    # setup failing redis cache and ignore exception settings
    setup_failing_redis_cache(settings)

    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=integration_type,
    )

    client = APIClient()
    url = reverse(
        "integrations:universal",
        kwargs={"integration_type": integration_type, "alert_channel_key": alert_receive_channel.token},
    )
    data = {"foo": "bar"}
    now = timezone.now()
    with patch("django.utils.timezone.now") as mock_now:
        mock_now.return_value = now
        response = client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK

    mock_create_alert.apply_async.assert_called_once_with(
        [],
        {
            "title": None,
            "message": None,
            "image_url": None,
            "link_to_upstream_details": None,
            "alert_receive_channel_pk": alert_receive_channel.pk,
            "integration_unique_data": None,
            "raw_request_data": data,
            "received_at": now.isoformat(),
        },
    )


@patch("apps.integrations.views.create_alertmanager_alerts")
@pytest.mark.django_db
def test_integration_grafana_endpoint_without_cache_has_alerts(
    mock_create_alertmanager_alerts, settings, make_organization_and_user, make_alert_receive_channel
):
    settings.DEBUG = False
    # setup failing redis cache and ignore exception settings
    setup_failing_redis_cache(settings)

    integration_type = "grafana"
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=integration_type,
    )

    client = APIClient()
    url = reverse("integrations:grafana", kwargs={"alert_channel_key": alert_receive_channel.token})

    data = {
        "alerts": [
            {
                "foo": 123,
            },
            {
                "foo": 456,
            },
        ]
    }
    now = timezone.now()
    with patch("django.utils.timezone.now") as mock_now:
        mock_now.return_value = now
        response = client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK

    mock_create_alertmanager_alerts.apply_async.assert_has_calls(
        [
            call((alert_receive_channel.pk, data["alerts"][0]), kwargs={"received_at": now.isoformat()}),
            call((alert_receive_channel.pk, data["alerts"][1]), kwargs={"received_at": now.isoformat()}),
        ]
    )


@patch("apps.integrations.views.create_alert")
@pytest.mark.parametrize(
    "integration_type",
    [
        arc_type
        for arc_type in INTEGRATION_TYPES
        if arc_type not in ["amazon_sns", "grafana", "alertmanager", "grafana_alerting", "maintenance"]
    ],
)
@pytest.mark.django_db
def test_integration_outdated_cached_model(
    mock_create_alert,
    make_organization_and_user,
    make_alert_receive_channel,
    integration_type,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=integration_type,
    )

    # set an invalid cache value for the requested integration
    cache_key = AlertChannelDefiningMixin.CACHE_KEY_SHORT_TERM + "_" + alert_receive_channel.token
    cache.set(cache_key, '{"some": "invalid json model"}')

    client = APIClient()
    url = reverse(
        "integrations:universal",
        kwargs={"integration_type": integration_type, "alert_channel_key": alert_receive_channel.token},
    )
    data = {"foo": "bar"}
    now = timezone.now()
    with patch("django.utils.timezone.now") as mock_now:
        mock_now.return_value = now
        response = client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK

    mock_create_alert.apply_async.assert_called_once_with(
        [],
        {
            "title": None,
            "message": None,
            "image_url": None,
            "link_to_upstream_details": None,
            "alert_receive_channel_pk": alert_receive_channel.pk,
            "integration_unique_data": None,
            "raw_request_data": data,
            "received_at": now.isoformat(),
        },
    )
