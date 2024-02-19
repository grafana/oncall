from unittest.mock import Mock, patch

import firebase_admin.messaging
import pytest
from firebase_admin.exceptions import FirebaseError
from requests import HTTPError

from apps.mobile_app import utils
from apps.mobile_app.models import FCMDevice
from apps.mobile_app.utils import add_stack_slug_to_message_title
from apps.oss_installation.models import CloudConnector

MOBILE_APP_BACKEND_ID = 5
CLOUD_LICENSE_NAME = "Cloud"
OPEN_SOURCE_LICENSE_NAME = "OpenSource"


@patch.object(FCMDevice, "send_message", return_value="ok")
@pytest.mark.django_db
def test_send_push_notification_cloud(
    mock_send_message,
    settings,
    make_organization_and_user,
):
    # create a user and connect a mobile device
    _, user = make_organization_and_user()
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")
    mock_message = {"foo": "bar"}

    # check FCM is contacted directly when using the cloud license
    settings.LICENSE = CLOUD_LICENSE_NAME
    settings.IS_OPEN_SOURCE = False

    succeeded = utils.send_push_notification(device, mock_message)
    assert succeeded
    mock_send_message.assert_called_once_with(mock_message)


@patch.object(FCMDevice, "send_message")
@pytest.mark.django_db
def test_send_push_notification_cloud_firebase_error(
    mock_send_message,
    settings,
    make_organization_and_user,
):
    mock_send_message.return_value = FirebaseError(code="test_error_code", message="test_error_message")

    # create a user and connect a mobile device
    _, user = make_organization_and_user()
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")
    mock_message = {"foo": "bar"}

    # check FCM is contacted directly when using the cloud license
    settings.LICENSE = CLOUD_LICENSE_NAME
    settings.IS_OPEN_SOURCE = False

    with pytest.raises(FirebaseError):
        utils.send_push_notification(device, mock_message)

    mock_send_message.assert_called_once_with(mock_message)


@patch.object(FCMDevice, "send_message")
@pytest.mark.parametrize(
    "ExceptionClass,exception_kwargs",
    [
        (firebase_admin.messaging.UnregisteredError, {"message": "test_error_message"}),
    ],
)
@pytest.mark.django_db
def test_send_push_notification_cloud_ignores_certain_errors(
    mock_send_message,
    settings,
    make_organization_and_user,
    ExceptionClass,
    exception_kwargs,
):
    mock_send_message.return_value = ExceptionClass(**exception_kwargs)

    # create a user and connect a mobile device
    _, user = make_organization_and_user()
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")
    mock_message = {"foo": "bar"}

    # check FCM is contacted directly when using the cloud license
    settings.LICENSE = CLOUD_LICENSE_NAME
    settings.IS_OPEN_SOURCE = False

    try:
        utils.send_push_notification(device, mock_message)
    except Exception:
        pytest.fail(f"send_push_notification should not raise an exception for {ExceptionClass.__name__} errors")

    mock_send_message.assert_called_once_with(mock_message)


@patch("apps.mobile_app.utils._send_push_notification_to_fcm_relay", return_value="ok")
@pytest.mark.django_db
def test_send_push_notification_oss(
    mock_send_push_notification_to_fcm_relay,
    settings,
    make_organization_and_user,
):
    settings.LICENSE = OPEN_SOURCE_LICENSE_NAME

    mock_error_cb = Mock()

    # create cloud connection
    CloudConnector.objects.create(cloud_url="test")

    # create a user and connect a mobile device
    _, user = make_organization_and_user()
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")
    mock_message = {"foo": "bar"}

    succeeded = utils.send_push_notification(device, mock_message, mock_error_cb)
    assert succeeded
    mock_error_cb.assert_not_called()
    mock_send_push_notification_to_fcm_relay.assert_called_once_with(mock_message)


@patch("apps.mobile_app.utils._send_push_notification_to_fcm_relay")
@pytest.mark.django_db
def test_send_push_notification_oss_no_cloud_connector(
    mock_send_push_notification_to_fcm_relay,
    settings,
    make_organization_and_user,
):
    settings.LICENSE = OPEN_SOURCE_LICENSE_NAME

    mock_error_cb = Mock()

    # create a user and connect a mobile device
    _, user = make_organization_and_user()
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")
    mock_message = {"foo": "bar"}

    succeeded = utils.send_push_notification(device, mock_message, mock_error_cb)

    assert not succeeded
    mock_error_cb.assert_called_once_with()
    mock_send_push_notification_to_fcm_relay.assert_not_called()


@patch("apps.mobile_app.utils._send_push_notification_to_fcm_relay")
@pytest.mark.django_db
def test_send_push_notification_oss_fcm_relay_returns_client_error(
    mock_send_push_notification_to_fcm_relay,
    settings,
    make_organization_and_user,
):
    settings.LICENSE = OPEN_SOURCE_LICENSE_NAME

    class MockResponse:
        status_code = 400

    mock_error_cb = Mock()
    mock_send_push_notification_to_fcm_relay.side_effect = HTTPError(response=MockResponse)

    # create cloud connection
    CloudConnector.objects.create(cloud_url="test")

    # create a user and connect a mobile device
    _, user = make_organization_and_user()
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")
    mock_message = {"foo": "bar"}

    succeeded = utils.send_push_notification(device, mock_message, mock_error_cb)
    assert not succeeded
    mock_send_push_notification_to_fcm_relay.assert_called_once_with(mock_message)


@patch("apps.mobile_app.utils._send_push_notification_to_fcm_relay")
@pytest.mark.django_db
def test_send_push_notification_oss_fcm_relay_returns_server_error(
    mock_send_push_notification_to_fcm_relay,
    settings,
    make_organization_and_user,
):
    settings.LICENSE = OPEN_SOURCE_LICENSE_NAME

    class MockResponse:
        status_code = 500

    mock_error_cb = Mock()
    mock_send_push_notification_to_fcm_relay.side_effect = HTTPError(response=MockResponse)

    # create cloud connection
    CloudConnector.objects.create(cloud_url="test")

    # create a user and connect a mobile device
    _, user = make_organization_and_user()
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")
    mock_message = {"foo": "bar"}

    with pytest.raises(HTTPError):
        utils.send_push_notification(device, mock_message, mock_error_cb)

    mock_error_cb.assert_not_called()
    mock_send_push_notification_to_fcm_relay.assert_called_once_with(mock_message)


@pytest.mark.django_db
def test_add_stack_slug_to_message_title(make_organization):
    test_stack_slug = "my-org"
    organization = make_organization(stack_slug=test_stack_slug)
    some_message_title = "Test title"
    expected_result = "[my-org] Test title"
    result = add_stack_slug_to_message_title(some_message_title, organization)
    assert result == expected_result
