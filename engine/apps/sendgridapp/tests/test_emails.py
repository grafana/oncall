# from unittest.mock import patch
#
# import pytest
# from django.urls import reverse
# from django.utils import timezone
# from rest_framework.test import APIClient
#
# from apps.sendgridapp.constants import SendgridEmailMessageStatuses
#
#
# @pytest.mark.skip(reason="email disabled")
# @patch("apps.integrations.helpers.inbound_emails.AllowOnlySendgrid.has_permission", return_value=True)
# @patch(
#     "apps.slack.helpers.slack_client.SlackClientWithErrorHandling.api_call",
#     return_value={"ok": True, "ts": timezone.now().timestamp()},
# )
# @pytest.mark.django_db
# @pytest.mark.parametrize("status", ["delivered", "bounce", "dropped"])
# def test_update_email_status(
#     mocked_slack_api_call,
#     mocked_sendgrid_permission,
#     make_team,
#     make_user_for_team,
#     make_email_message,
#     make_alert_receive_channel,
#     make_alert_group,
#     status,
# ):
#     """The test for Email message status update via api"""
#     amixr_team = make_team()
#     admin = make_user_for_team(amixr_team, role=ROLE_ADMIN)
#     alert_receive_channel = make_alert_receive_channel(amixr_team)
#     alert_group = make_alert_group(alert_receive_channel)
#     email_message = make_email_message(
#         receiver=admin, status=SendgridEmailMessageStatuses.ACCEPTED, represents_alert_group=alert_group
#     )
#     client = APIClient()
#     url = reverse("sendgridapp:email_status_event")
#
#     data = [
#         {
#             "message_uuid": str(email_message.message_uuid),
#             "event": status,
#         }
#     ]
#     response = client.post(
#         url,
#         data,
#         format="json",
#     )
#
#     assert response.status_code == 204
#     assert response.data == ""
#     email_message.refresh_from_db()
#     assert email_message.status == SendgridEmailMessageStatuses.DETERMINANT[status]
