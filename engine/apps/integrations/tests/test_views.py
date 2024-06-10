from unittest.mock import call, patch

import pytest
from django import test
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import OperationalError
from django.urls import reverse
from django.utils import timezone
from pytest_django.plugin import DjangoDbBlocker
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertReceiveChannel
from apps.alerts.models.alert_receive_channel import random_token_generator
from apps.integrations.mixins import AlertChannelDefiningMixin
from apps.integrations.mixins.alert_channel_defining_mixin import CHANNEL_DOES_NOT_EXIST_PLACEHOLDER
from apps.integrations.views import UniversalAPIView

# https://github.com/pytest-dev/pytest-xdist/issues/432#issuecomment-528510433
INTEGRATION_TYPES = sorted(AlertReceiveChannel.INTEGRATION_TYPES)


class DatabaseBlocker(DjangoDbBlocker):
    """Customize pytest_django db blocker to raise OperationalError exception."""

    def __init__(self, *args, **kwargs):
        """
        Override the constructor to get around this:
        https://github.com/pytest-dev/pytest-django/blob/v4.8.0/pytest_django/plugin.py#L778-L782
        """
        self._history = []
        self._real_ensure_connection = None

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
    AlertChannelDefiningMixin().update_alert_receive_channel_fallback_cache()

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
    AlertChannelDefiningMixin().update_alert_receive_channel_fallback_cache()

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


@patch("django.core.cache.cache.get", wraps=cache.get)
@patch("django.core.cache.cache.set", wraps=cache.set)
@patch(
    "apps.alerts.models.AlertReceiveChannel.objects.get",
    wraps=AlertReceiveChannel.objects.get,
)
@pytest.mark.parametrize(
    "integration_type",
    [arc_type for arc_type in INTEGRATION_TYPES],
)
@pytest.mark.django_db
def test_non_existent_integration_does_not_repeat_access_db(
    mock_db_get, mock_cache_set, mock_cache_get, integration_type
):
    attempts = 5
    non_existent_integration_token = random_token_generator()
    cache_key = AlertChannelDefiningMixin.CACHE_KEY_SHORT_TERM + "_" + non_existent_integration_token
    client = APIClient()
    url = reverse(
        "integrations:universal",
        kwargs={"integration_type": integration_type, "alert_channel_key": non_existent_integration_token},
    )

    for _ in range(attempts):
        data = {"foo": "bar"}
        response = client.post(url, data, format="json")
        mock_cache_get.assert_called_with(cache_key)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    assert mock_cache_get.call_count == attempts
    mock_cache_set.assert_called_once_with(
        cache_key, CHANNEL_DOES_NOT_EXIST_PLACEHOLDER, AlertChannelDefiningMixin.CACHE_SHORT_TERM_TIMEOUT
    )
    mock_db_get.assert_called_once_with(token=non_existent_integration_token)


@patch("django.core.cache.cache.get", wraps=cache.get)
@patch("django.core.cache.cache.set", wraps=cache.set)
@patch(
    "apps.alerts.models.AlertReceiveChannel.objects.get",
    wraps=AlertReceiveChannel.objects.get,
)
@pytest.mark.parametrize(
    "integration_type",
    [arc_type for arc_type in INTEGRATION_TYPES],
)
@pytest.mark.django_db
def test_deleted_integration_does_not_repeat_access_db(
    mock_db_get,
    mock_cache_set,
    mock_cache_get,
    make_organization_and_user,
    make_alert_receive_channel,
    integration_type,
):
    attempts = 5
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=integration_type,
    )

    cache_key = AlertChannelDefiningMixin.CACHE_KEY_SHORT_TERM + "_" + alert_receive_channel.token
    alert_receive_channel.delete()

    client = APIClient()
    url = reverse(
        "integrations:universal",
        kwargs={"integration_type": integration_type, "alert_channel_key": alert_receive_channel.token},
    )

    mock_cache_get.reset_mock()
    for _ in range(attempts):
        data = {"foo": "bar"}
        response = client.post(url, data, format="json")
        mock_cache_get.assert_called_with(cache_key)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    assert mock_cache_get.call_count == attempts
    mock_cache_set.assert_called_once_with(
        cache_key, CHANNEL_DOES_NOT_EXIST_PLACEHOLDER, AlertChannelDefiningMixin.CACHE_SHORT_TERM_TIMEOUT
    )
    mock_db_get.assert_called_once_with(token=alert_receive_channel.token)
