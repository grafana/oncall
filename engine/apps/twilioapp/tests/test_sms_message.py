from unittest import mock

import pytest
from django.urls import reverse
from django.utils import timezone
from django.utils.datastructures import MultiValueDict
from django.utils.http import urlencode
from rest_framework.test import APIClient

from apps.base.models import UserNotificationPolicy
from apps.twilioapp.models import TwilioSMS, TwilioSMSstatuses


@pytest.fixture
def make_twilio_sms(
    make_organization_and_user,
    make_alert_receive_channel,
    make_user_notification_policy,
    make_alert_group,
    make_alert,
    make_sms_record,
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
    sms_record = make_sms_record(
        receiver=user,
        represents_alert_group=alert_group,
        notification_policy=notification_policy,
    )
    return TwilioSMS.objects.create(sid="SMa12312312a123a123123c6dd2f1aee77", sms_record=sms_record)


@pytest.mark.django_db
def test_forbidden_requests(make_twilio_sms):
    """Tests check inaccessibility of twilio urls for unauthorized requests"""
    twilio_sms = make_twilio_sms

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
    data = {"MessageSid": twilio_sms.sid, "MessageStatus": "delivered", "AccountSid": "TopSecretAccountSid"}

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
@pytest.mark.django_db
def test_update_status(mock_has_permission, mock_slack_api_call, make_twilio_sms):
    """The test for SMSMessage status update via api"""
    twilio_sms = make_twilio_sms
    mock_has_permission.return_value = True
    for status in ["delivered", "failed", "undelivered"]:
        data = {
            "MessageSid": twilio_sms.sid,
            "MessageStatus": status,
            "AccountSid": "Because of mock_has_permission there are may be any value",
        }
        client = APIClient()
        response = client.post(
            path=reverse("twilioapp:sms_status_events"),
            data=urlencode(MultiValueDict(data), doseq=True),
            content_type="application/x-www-form-urlencoded",
        )
        assert response.status_code == 204
        assert response.data == ""
        twilio_sms.refresh_from_db()
        assert twilio_sms.status == TwilioSMSstatuses.DETERMINANT[status]


@mock.patch("apps.twilioapp.views.AllowOnlyTwilio.has_permission")
@pytest.mark.django_db
def test_update_status_for_bundled_notifications(
    mock_has_permission,
    mock_slack_api_call,
    make_organization_and_user,
    make_alert_receive_channel,
    make_user_notification_policy,
    make_user_notification_bundle,
    make_alert_group,
    make_sms_record,
):
    """The test for SMSMessage status update via api for notification bundle"""
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group_1 = make_alert_group(alert_receive_channel)
    alert_group_2 = make_alert_group(alert_receive_channel)
    notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SMS,
    )

    notification_bundle = make_user_notification_bundle(
        user, UserNotificationPolicy.NotificationChannel.SMS, notification_task_id="test_task_id", eta=timezone.now()
    )
    notification_bundle.append_notification(alert_group_1, notification_policy)
    notification_bundle.append_notification(alert_group_2, notification_policy)
    bundle_uuid = "test_notifications_bundle"

    notification_bundle.notifications.update(bundle_uuid=bundle_uuid)
    sms_record = make_sms_record(
        receiver=user,
        represents_bundle_uuid=bundle_uuid,
        notification_policy=notification_policy,
    )
    twilio_sms = TwilioSMS.objects.create(sid="SMa12312312a123a123123c6dd2f1aee77", sms_record=sms_record)

    mock_has_permission.return_value = True
    status = "delivered"
    data = {
        "MessageSid": twilio_sms.sid,
        "MessageStatus": status,
        "AccountSid": "Because of mock_has_permission there are may be any value",
    }
    assert user.personal_log_records.count() == 0

    client = APIClient()
    response = client.post(
        path=reverse("twilioapp:sms_status_events"),
        data=urlencode(MultiValueDict(data), doseq=True),
        content_type="application/x-www-form-urlencoded",
    )
    assert response.status_code == 204
    assert response.data == ""
    twilio_sms.refresh_from_db()
    assert twilio_sms.status == TwilioSMSstatuses.DETERMINANT[status]

    assert user.personal_log_records.count() == 2
