from unittest import mock

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from django.utils.http import urlencode
from rest_framework.test import APIClient

from apps.base.models import UserNotificationPolicy
from apps.twilioapp.models import TwilioCallStatuses, TwilioPhoneCall


@pytest.fixture
def make_twilio_phone_call(
    make_organization_and_user,
    make_alert_receive_channel,
    make_user_notification_policy,
    make_alert_group,
    make_phone_call_record,
    make_alert,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data="{}")
    notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.PHONE_CALL,
    )
    phone_call_record = make_phone_call_record(
        receiver=user,
        represents_alert_group=alert_group,
        notification_policy=notification_policy,
    )
    return TwilioPhoneCall.objects.create(sid="SMa12312312a123a123123c6dd2f1aee77", phone_call_record=phone_call_record)


@pytest.mark.django_db
def test_forbidden_requests(make_twilio_phone_call):
    """Tests check inaccessibility of twilio urls for unauthorized requests"""
    twilio_phone_call = make_twilio_phone_call

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
    data = {"CallSid": twilio_phone_call.sid, "CallStatus": "completed", "AccountSid": "TopSecretAccountSid"}

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
@pytest.mark.django_db
def test_update_status(mock_has_permission, make_twilio_phone_call):
    """The test for PhoneCall status update via api"""
    twilio_phone_call = make_twilio_phone_call

    mock_has_permission.return_value = True

    for status in ["in-progress", "completed", "busy", "failed", "no-answer", "canceled"]:
        data = {
            "CallSid": twilio_phone_call.sid,
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

        twilio_phone_call.refresh_from_db()
        assert twilio_phone_call.status == TwilioCallStatuses.DETERMINANT[status]


@mock.patch("apps.twilioapp.views.AllowOnlyTwilio.has_permission")
@mock.patch("apps.twilioapp.gather.get_gather_url")
@pytest.mark.django_db
def test_acknowledge_by_phone(mock_has_permission, mock_get_gather_url, make_twilio_phone_call):
    twilio_phone_call = make_twilio_phone_call
    alert_group = twilio_phone_call.phone_call_record.represents_alert_group
    mock_has_permission.return_value = True
    mock_get_gather_url.return_value = reverse("twilioapp:gather")

    data = {
        "CallSid": twilio_phone_call.sid,
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
@mock.patch("apps.twilioapp.gather.get_gather_url")
@pytest.mark.django_db
def test_resolve_by_phone(mock_has_permission, mock_get_gather_url, make_twilio_phone_call):
    twilio_phone_call = make_twilio_phone_call

    mock_has_permission.return_value = True
    mock_get_gather_url.return_value = reverse("twilioapp:gather")

    data = {
        "CallSid": twilio_phone_call.sid,
        "Digits": "2",
        "AccountSid": "Because of mock_has_permission there are may be any value",
    }

    alert_group = twilio_phone_call.phone_call_record.represents_alert_group
    assert alert_group.resolved is False

    client = APIClient()
    response = client.post(
        reverse("twilioapp:gather"),
        data=urlencode(MultiValueDict(data), doseq=True),
        content_type="application/x-www-form-urlencoded",
    )

    content = response.content.decode("utf-8")
    content = BeautifulSoup(content, features="xml").findAll(string=True)

    assert response.status_code == 200
    assert "You have pressed digit 2" in content

    alert_group.refresh_from_db()
    assert alert_group.resolved is True


@mock.patch("apps.twilioapp.views.AllowOnlyTwilio.has_permission")
@mock.patch("apps.twilioapp.gather.get_gather_url")
@pytest.mark.django_db
def test_silence_by_phone(mock_has_permission, mock_get_gather_url, make_twilio_phone_call):
    twilio_phone_call = make_twilio_phone_call

    mock_has_permission.return_value = True
    mock_get_gather_url.return_value = reverse("twilioapp:gather")

    data = {
        "CallSid": twilio_phone_call.sid,
        "Digits": "3",
        "AccountSid": "Because of mock_has_permission there are may be any value",
    }

    alert_group = twilio_phone_call.phone_call_record.represents_alert_group
    assert alert_group.resolved is False

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
@mock.patch("apps.twilioapp.gather.get_gather_url")
@pytest.mark.django_db
def test_wrong_pressed_digit(mock_has_permission, mock_get_gather_url, make_twilio_phone_call):
    twilio_phone_call = make_twilio_phone_call

    mock_has_permission.return_value = True
    mock_get_gather_url.return_value = reverse("twilioapp:gather")

    data = {
        "CallSid": twilio_phone_call.sid,
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
    content = BeautifulSoup(content, features="xml").findAll(string=True)

    assert response.status_code == 200
    assert "Wrong digit" in content
