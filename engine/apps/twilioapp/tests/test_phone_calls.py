import urllib
from unittest import mock

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse
from django.utils import timezone
from django.utils.datastructures import MultiValueDict
from django.utils.http import urlencode
from rest_framework.test import APIClient

from apps.base.models import UserNotificationPolicy
from apps.twilioapp.constants import TwilioCallStatuses
from apps.twilioapp.models import PhoneCall
from apps.twilioapp.utils import get_gather_message


class FakeTwilioCall:
    def __init__(self):
        self.sid = "123"
        self.status = TwilioCallStatuses.COMPLETED


@pytest.fixture
def phone_call_setup(
    make_organization_and_user,
    make_alert_receive_channel,
    make_user_notification_policy,
    make_alert_group,
    make_alert,
    make_phone_call,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(
        alert_group,
        raw_request_data={
            "status": "firing",
            "labels": {
                "alertname": "TestAlert",
                "region": "eu-1",
            },
            "annotations": {},
            "startsAt": "2018-12-25T15:47:47.377363608Z",
            "endsAt": "0001-01-01T00:00:00Z",
            "generatorURL": "",
        },
    )

    notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.PHONE_CALL,
    )

    phone_call = make_phone_call(
        receiver=user,
        status=TwilioCallStatuses.QUEUED,
        represents_alert_group=alert_group,
        sid="SMa12312312a123a123123c6dd2f1aee77",
        notification_policy=notification_policy,
    )

    return phone_call, alert_group


@pytest.mark.django_db
def test_phone_call_creation(phone_call_setup):
    phone_call, _ = phone_call_setup
    assert PhoneCall.objects.count() == 1
    assert phone_call == PhoneCall.objects.first()


@pytest.mark.django_db
def test_forbidden_requests(phone_call_setup):
    """Tests check inaccessibility of twilio urls for unauthorized requests"""
    phone_call, _ = phone_call_setup

    # empty data case
    data = {}

    client = APIClient()
    response = client.post(
        reverse("twilioapp:call_status_events"),
        data=urlencode(MultiValueDict(data), doseq=True),
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 403
    assert response.data["detail"] == "You do not have permission to perform this action."

    # wrong AccountSid data
    data = {"CallSid": phone_call.sid, "CallStatus": "completed", "AccountSid": "TopSecretAccountSid"}

    client = APIClient()
    response = client.post(
        path=reverse("twilioapp:call_status_events"),
        data=urlencode(MultiValueDict(data), doseq=True),
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 403
    assert response.data["detail"] == "You do not have permission to perform this action."

    # absent CallSid data
    data = {"CallStatus": "completed", "AccountSid": "TopSecretAccountSid"}

    client = APIClient()
    response = client.post(
        path=reverse("twilioapp:call_status_events"),
        data=urlencode(MultiValueDict(data), doseq=True),
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 403
    assert response.data["detail"] == "You do not have permission to perform this action."


@mock.patch("apps.twilioapp.views.AllowOnlyTwilio.has_permission")
@mock.patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call")
@pytest.mark.django_db
def test_update_status(mock_has_permission, mock_slack_api_call, phone_call_setup):
    """The test for PhoneCall status update via api"""
    phone_call, _ = phone_call_setup

    mock_has_permission.return_value = True

    for status in ["in-progress", "completed", "busy", "failed", "no-answer", "canceled"]:
        mock_slack_api_call.return_value = {"ok": True, "ts": timezone.now().timestamp()}

        data = {
            "CallSid": phone_call.sid,
            "CallStatus": status,
            "AccountSid": "Because of mock_has_permission there are may be any value",
        }

        client = APIClient()
        response = client.post(
            path=reverse("twilioapp:call_status_events"),
            data=urlencode(MultiValueDict(data), doseq=True),
            content_type="application/x-www-form-urlencoded",
        )

        assert response.status_code == 204
        assert response.data == ""

        phone_call.refresh_from_db()
        assert phone_call.status == TwilioCallStatuses.DETERMINANT[status]


@mock.patch("apps.twilioapp.views.AllowOnlyTwilio.has_permission")
@mock.patch("apps.twilioapp.utils.get_gather_url")
@pytest.mark.django_db
def test_acknowledge_by_phone(mock_has_permission, mock_get_gather_url, phone_call_setup):
    phone_call, alert_group = phone_call_setup

    mock_has_permission.return_value = True
    mock_get_gather_url.return_value = reverse("twilioapp:gather")

    data = {
        "CallSid": phone_call.sid,
        "Digits": "1",
        "AccountSid": "Because of mock_has_permission there are may be any value",
    }

    assert alert_group.acknowledged is False

    client = APIClient()
    response = client.post(
        reverse("twilioapp:gather"),
        data=urlencode(MultiValueDict(data), doseq=True),
        content_type="application/x-www-form-urlencoded",
    )

    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "You have pressed digit 1" in content

    alert_group.refresh_from_db()
    assert alert_group.acknowledged is True


@mock.patch("apps.twilioapp.views.AllowOnlyTwilio.has_permission")
@mock.patch("apps.twilioapp.utils.get_gather_url")
@pytest.mark.django_db
def test_resolve_by_phone(mock_has_permission, mock_get_gather_url, phone_call_setup):
    phone_call, alert_group = phone_call_setup

    mock_has_permission.return_value = True
    mock_get_gather_url.return_value = reverse("twilioapp:gather")

    data = {
        "CallSid": phone_call.sid,
        "Digits": "2",
        "AccountSid": "Because of mock_has_permission there are may be any value",
    }

    assert alert_group.resolved is False

    client = APIClient()
    response = client.post(
        reverse("twilioapp:gather"),
        data=urlencode(MultiValueDict(data), doseq=True),
        content_type="application/x-www-form-urlencoded",
    )

    content = response.content.decode("utf-8")
    content = BeautifulSoup(content, features="html.parser").findAll(text=True)

    assert response.status_code == 200
    assert "You have pressed digit 2" in content

    alert_group.refresh_from_db()
    assert alert_group.resolved is True


@mock.patch("apps.twilioapp.views.AllowOnlyTwilio.has_permission")
@mock.patch("apps.twilioapp.utils.get_gather_url")
@pytest.mark.django_db
def test_silence_by_phone(mock_has_permission, mock_get_gather_url, phone_call_setup):
    phone_call, alert_group = phone_call_setup

    mock_has_permission.return_value = True
    mock_get_gather_url.return_value = reverse("twilioapp:gather")

    data = {
        "CallSid": phone_call.sid,
        "Digits": "3",
        "AccountSid": "Because of mock_has_permission there are may be any value",
    }

    assert alert_group.silenced_until is None

    client = APIClient()
    response = client.post(
        reverse("twilioapp:gather"),
        data=urlencode(MultiValueDict(data), doseq=True),
        content_type="application/x-www-form-urlencoded",
    )

    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "You have pressed digit 3" in content

    alert_group.refresh_from_db()
    assert alert_group.silenced_until is not None


@mock.patch("apps.twilioapp.views.AllowOnlyTwilio.has_permission")
@mock.patch("apps.twilioapp.utils.get_gather_url")
@pytest.mark.django_db
def test_wrong_pressed_digit(mock_has_permission, mock_get_gather_url, phone_call_setup):
    phone_call, _ = phone_call_setup

    mock_has_permission.return_value = True
    mock_get_gather_url.return_value = reverse("twilioapp:gather")

    data = {
        "CallSid": phone_call.sid,
        "Digits": "0",
        "AccountSid": "Because of mock_has_permission there are may be any value",
    }

    client = APIClient()
    response = client.post(
        path=reverse("twilioapp:gather"),
        data=urlencode(MultiValueDict(data), doseq=True),
        content_type="application/x-www-form-urlencoded",
    )

    content = response.content.decode("utf-8")
    content = BeautifulSoup(content, features="html.parser").findAll(text=True)

    assert response.status_code == 200
    assert "Wrong digit" in content


@mock.patch("apps.twilioapp.twilio_client.Client")
@pytest.mark.django_db
def test_make_cloud_phone_call_not_gathering_digit(mock_twilio_client, make_organization, make_user):
    organization = make_organization()
    user = make_user(organization=organization, _verified_phone_number="9999555")
    mock_twilio_client.return_value.calls.create.return_value = FakeTwilioCall()

    PhoneCall.make_grafana_cloud_call(user, "the message")

    gather_message = urllib.parse.quote(get_gather_message())
    assert gather_message not in mock_twilio_client.return_value.calls.create.call_args.kwargs["url"]


@mock.patch("apps.twilioapp.twilio_client.Client")
@pytest.mark.django_db
def test_make_phone_call_gathering_digit(
    mock_twilio_client,
    make_organization,
    make_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    organization = make_organization()
    user = make_user(organization=organization, _verified_phone_number="9999555")
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.PHONE_CALL,
    )
    make_alert(
        alert_group,
        raw_request_data={
            "status": "firing",
            "labels": {
                "alertname": "TestAlert",
                "region": "eu-1",
            },
            "annotations": {},
            "startsAt": "2018-12-25T15:47:47.377363608Z",
            "endsAt": "0001-01-01T00:00:00Z",
            "generatorURL": "",
        },
    )
    mock_twilio_client.return_value.calls.create.return_value = FakeTwilioCall()

    PhoneCall.make_call(user, alert_group, notification_policy)

    gather_message = urllib.parse.quote(get_gather_message())
    assert gather_message in mock_twilio_client.return_value.calls.create.call_args.kwargs["url"]
