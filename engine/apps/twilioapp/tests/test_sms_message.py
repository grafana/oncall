from unittest import mock

import pytest
from django.urls import reverse
from django.utils import timezone
from django.utils.datastructures import MultiValueDict
from django.utils.http import urlencode
from rest_framework.test import APIClient

from apps.base.models import UserNotificationPolicy
from apps.twilioapp.constants import TwilioMessageStatuses
from apps.twilioapp.models import SMSMessage


@pytest.fixture
def sms_message_setup(
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
        notify_by=UserNotificationPolicy.NotificationChannel.SMS,
    )

    sms_message = SMSMessage.objects.create(
        represents_alert_group=alert_group,
        receiver=user,
        sid="SMa12312312a123a123123c6dd2f1aee77",
        status=TwilioMessageStatuses.QUEUED,
        notification_policy=notification_policy,
    )

    return sms_message, alert_group


@pytest.mark.django_db
def test_sms_message_creation(sms_message_setup):
    sms_message, _ = sms_message_setup

    assert SMSMessage.objects.count() == 1
    assert sms_message == SMSMessage.objects.first()


@pytest.mark.django_db
def test_forbidden_requests(sms_message_setup):
    """Tests check inaccessibility of twilio urls for unauthorized requests"""
    sms_message, _ = sms_message_setup

    # empty data case
    data = {}

    client = APIClient()
    response = client.post(
        path=reverse("twilioapp:sms_status_events"),
        data=urlencode(MultiValueDict(data), doseq=True),
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 403
    assert response.data["detail"] == "You do not have permission to perform this action."

    # wrong AccountSid data
    data = {"MessageSid": sms_message.sid, "MessageStatus": "delivered", "AccountSid": "TopSecretAccountSid"}

    response = client.post(
        path=reverse("twilioapp:sms_status_events"),
        data=urlencode(MultiValueDict(data), doseq=True),
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 403
    assert response.data["detail"] == "You do not have permission to perform this action."

    # absent MessageSid data
    data = {"MessageStatus": "delivered", "AccountSid": "TopSecretAccountSid"}

    response = client.post(
        path=reverse("twilioapp:sms_status_events"),
        data=urlencode(MultiValueDict(data), doseq=True),
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 403
    assert response.data["detail"] == "You do not have permission to perform this action."


@mock.patch("apps.twilioapp.views.AllowOnlyTwilio.has_permission")
@mock.patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call")
@pytest.mark.django_db
def test_update_status(mock_has_permission, mock_slack_api_call, sms_message_setup):
    """The test for SMSMessage status update via api"""
    sms_message, _ = sms_message_setup

    # https://stackoverflow.com/questions/50157543/unittest-django-mock-external-api-what-is-proper-way
    # Define response for the fake SlackClientWithErrorHandling.api_call
    mock_has_permission.return_value = True

    for status in ["delivered", "failed", "undelivered"]:
        mock_slack_api_call.return_value = {"ok": True, "ts": timezone.now().timestamp()}

        data = {
            "MessageSid": sms_message.sid,
            "MessageStatus": status,
            "AccountSid": "Because of mock_has_permission there are may be any value",
        }
        # https://stackoverflow.com/questions/11571474/djangos-test-client-with-multiple-values-for-data-keys

        client = APIClient()
        response = client.post(
            path=reverse("twilioapp:sms_status_events"),
            data=urlencode(MultiValueDict(data), doseq=True),
            content_type="application/x-www-form-urlencoded",
        )

        assert response.status_code == 204
        assert response.data == ""

        sms_message.refresh_from_db()
        assert sms_message.status == TwilioMessageStatuses.DETERMINANT[status]
