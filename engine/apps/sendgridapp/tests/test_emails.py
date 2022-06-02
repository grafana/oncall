# from unittest.mock import patch
#
# import pytest
# from django.urls import reverse
# from django.utils import timezone
# from rest_framework.test import APIClient
#
# from apps.sendgridapp.constants import SendgridEmailMessageStatuses
# from apps.sendgridapp.verification_token import email_verification_token_generator
#
#
# @pytest.mark.skip(reason="email disabled")
# @pytest.mark.django_db
# def test_email_verification(
#     make_team,
#     make_user_for_team,
#     make_email_message,
#     make_alert_receive_channel,
#     make_alert_group,
# ):
#     amixr_team = make_team()
#     admin = make_user_for_team(amixr_team, role=ROLE_ADMIN)
#     alert_receive_channel = make_alert_receive_channel(amixr_team)
#     alert_group = make_alert_group(alert_receive_channel)
#     make_email_message(
#         receiver=admin, status=SendgridEmailMessageStatuses.ACCEPTED, represents_alert_group=alert_group
#     ),
#     client = APIClient()
#     correct_token = email_verification_token_generator.make_token(admin)
#     url = reverse("sendgridapp:verify_email", kwargs={"token": correct_token, "uid": admin.pk, "slackteam": None})
#     response = client.get(url, content_type="application/json")
#     assert response.status_code == 200
#     admin.refresh_from_db()
#     assert admin.email_verified is True
#
#
# @pytest.mark.skip(reason="email disabled")
# @pytest.mark.django_db
# def test_email_verification_incorrect_token(
#     make_team,
#     make_user_for_team,
#     make_email_message,
#     make_alert_receive_channel,
#     make_alert_group,
# ):
#     amixr_team = make_team()
#     admin = make_user_for_team(amixr_team, role=ROLE_ADMIN)
#     alert_receive_channel = make_alert_receive_channel(amixr_team)
#     alert_group = make_alert_group(alert_receive_channel)
#     make_email_message(
#         receiver=admin, status=SendgridEmailMessageStatuses.ACCEPTED, represents_alert_group=alert_group
#     ),
#
#     client = APIClient()
#     url = reverse("sendgridapp:verify_email", kwargs={"token": "incorrect_token", "uid": admin.pk, "slackteam": None})
#
#     response = client.get(path=url, content_type="application/json")
#     assert response.status_code == 403
#     admin.refresh_from_db()
#     assert admin.email_verified is False
#
#
# @pytest.mark.skip(reason="email disabled")
# @pytest.mark.django_db
# def test_email_verification_incorrect_uid(
#     make_team,
#     make_user_for_team,
#     make_email_message,
#     make_alert_receive_channel,
#     make_alert_group,
# ):
#     amixr_team = make_team()
#     admin = make_user_for_team(amixr_team, role=ROLE_ADMIN)
#     alert_receive_channel = make_alert_receive_channel(amixr_team)
#     alert_group = make_alert_group(alert_receive_channel)
#     make_email_message(
#         receiver=admin, status=SendgridEmailMessageStatuses.ACCEPTED, represents_alert_group=alert_group
#     ),
#     client = APIClient()
#
#     correct_token = email_verification_token_generator.make_token(admin)
#     url = reverse(
#         "sendgridapp:verify_email", kwargs={"token": correct_token, "uid": 100, "slackteam": None}  # incorrect user uid
#     )
#     response = client.get(path=url, content_type="application/json")
#     assert response.status_code == 403
#     admin.refresh_from_db()
#     assert admin.email_verified is False
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
