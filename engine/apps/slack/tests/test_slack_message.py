from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.slack.client import SlackClient
from apps.slack.errors import SlackAPIError
from apps.slack.models import SlackMessage
from apps.slack.tests.conftest import build_slack_response


@pytest.fixture
def slack_message_setup(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_slack_channel,
    make_slack_message,
):
    def _slack_message_setup(cached_permalink):
        organization, _, slack_team_identity, _ = make_organization_and_user_with_slack_identities()
        integration = make_alert_receive_channel(organization)
        alert_group = make_alert_group(integration)
        slack_channel = make_slack_channel(slack_team_identity)

        return make_slack_message(slack_channel, alert_group=alert_group, cached_permalink=cached_permalink)

    return _slack_message_setup


@patch.object(
    SlackClient,
    "chat_getPermalink",
    return_value=build_slack_response({"ok": True, "permalink": "test_permalink"}),
)
@pytest.mark.django_db
def test_slack_message_permalink(mock_slack_api_call, slack_message_setup):
    slack_message = slack_message_setup(cached_permalink=None)
    assert slack_message.permalink == "test_permalink"
    mock_slack_api_call.assert_called_once()


@patch.object(
    SlackClient,
    "chat_getPermalink",
    side_effect=SlackAPIError(response=build_slack_response({"ok": False, "error": "message_not_found"})),
)
@pytest.mark.django_db
def test_slack_message_permalink_error(mock_slack_api_call, slack_message_setup):
    slack_message = slack_message_setup(cached_permalink=None)
    assert slack_message.permalink is None
    mock_slack_api_call.assert_called_once()


@patch.object(
    SlackClient,
    "chat_getPermalink",
    return_value=build_slack_response({"ok": True, "permalink": "test_permalink"}),
)
@pytest.mark.django_db
def test_slack_message_permalink_cache(mock_slack_api_call, slack_message_setup):
    slack_message = slack_message_setup(cached_permalink="cached_permalink")
    assert slack_message.permalink == "cached_permalink"
    mock_slack_api_call.assert_not_called()


@patch.object(
    SlackClient,
    "chat_getPermalink",
    return_value=build_slack_response({"ok": False, "error": "account_inactive"}),
)
@pytest.mark.django_db
def test_slack_message_permalink_token_revoked(mock_slack_api_call, slack_message_setup):
    slack_message = slack_message_setup(cached_permalink=None)
    slack_message.slack_team_identity.detected_token_revoked = timezone.now()
    slack_message.slack_team_identity.save()

    assert slack_message.slack_team_identity is not None
    assert slack_message.permalink is None

    mock_slack_api_call.assert_not_called()


@pytest.mark.django_db
def test_send_slack_notification(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_user_notification_policy,
    make_slack_channel,
    make_slack_message,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()

    # set up notification policy and alert group
    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SLACK,
    )
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(slack_channel, alert_group=alert_group)

    with patch("apps.slack.client.SlackClient.conversations_members") as mock_members:
        mock_members.return_value = {"members": [slack_user_identity.slack_id]}
        slack_message.send_slack_notification(user, alert_group, notification_policy)

    log_record = notification_policy.personal_log_records.last()
    assert log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS


@pytest.mark.django_db
def test_slack_message_deep_link(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    organization, _, slack_team_identity, _ = make_organization_and_user_with_slack_identities()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(slack_channel, alert_group=alert_group)

    expected = (
        f"https://slack.com/app_redirect?channel={slack_channel.slack_id}"
        f"&team={slack_team_identity.slack_id}&message={slack_message.slack_id}"
    )
    assert slack_message.deep_link == expected


class TestSlackMessageUpdateAlertGroupsMessage:
    @patch("apps.slack.models.slack_message.update_alert_group_slack_message")
    @pytest.mark.django_db
    def test_update_alert_groups_message_no_alert_group(
        self,
        mock_update_alert_group_slack_message,
        make_organization_with_slack_team_identity,
        make_slack_channel,
        make_slack_message,
    ):
        """
        Test that the method exits early if alert_group is None.
        """
        _, slack_team_identity = make_organization_with_slack_team_identity()
        slack_channel = make_slack_channel(slack_team_identity)
        slack_message = make_slack_message(slack_channel)

        slack_message.update_alert_groups_message(debounce=True)

        # Ensure no task is scheduled
        mock_update_alert_group_slack_message.apply_async.assert_not_called()

    @patch("apps.slack.models.slack_message.update_alert_group_slack_message")
    @pytest.mark.django_db
    def test_update_alert_groups_message_active_task_exists(
        self,
        mock_update_alert_group_slack_message,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_alert_group,
        make_slack_channel,
        make_slack_message,
    ):
        """
        Test that the method exits early if a task ID is set in the cache and debounce is True.
        """
        task_id = "some-task-id"

        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        slack_channel = make_slack_channel(slack_team_identity)

        slack_message = make_slack_message(slack_channel, alert_group=alert_group)
        slack_message.set_active_update_task_id(task_id)

        slack_message.update_alert_groups_message(debounce=True)

        # Ensure no task is scheduled
        mock_update_alert_group_slack_message.apply_async.assert_not_called()

        # Ensure task ID in the cache remains unchanged
        assert slack_message.get_active_update_task_id() == task_id

    @patch("apps.slack.models.slack_message.celery_uuid")
    @patch("apps.slack.models.slack_message.update_alert_group_slack_message")
    @pytest.mark.django_db
    def test_update_alert_groups_message_last_updated_none(
        self,
        mock_update_alert_group_slack_message,
        mock_celery_uuid,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_slack_channel,
        make_slack_message,
        make_alert_group,
    ):
        """
        Test that the method handles last_updated being None and schedules with default debounce interval.
        """
        task_id = "some-task-id"
        mock_celery_uuid.return_value = task_id

        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)

        slack_channel = make_slack_channel(slack_team_identity)
        slack_message = make_slack_message(slack_channel, alert_group=alert_group, last_updated=None)

        assert slack_message.get_active_update_task_id() is None

        slack_message.update_alert_groups_message(debounce=True)

        # Verify that apply_async was called with correct countdown
        mock_update_alert_group_slack_message.apply_async.assert_called_once_with(
            (slack_message.pk,),
            countdown=SlackMessage.ALERT_GROUP_UPDATE_DEBOUNCE_INTERVAL_SECONDS,
            task_id=task_id,
        )

        # Verify task ID is set in the cache
        assert slack_message.get_active_update_task_id() == task_id

    @patch("apps.slack.models.slack_message.celery_uuid")
    @patch("apps.slack.models.slack_message.update_alert_group_slack_message")
    @pytest.mark.django_db
    def test_update_alert_groups_message_schedules_task_correctly(
        self,
        mock_update_alert_group_slack_message,
        mock_celery_uuid,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_slack_channel,
        make_slack_message,
        make_alert_group,
    ):
        """
        Test that the method schedules the task with correct countdown and updates the task ID in the cache
        """
        task_id = "some-task-id"
        mock_celery_uuid.return_value = task_id

        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)

        slack_channel = make_slack_channel(slack_team_identity)
        slack_message = make_slack_message(
            slack_channel,
            alert_group=alert_group,
            last_updated=timezone.now() - timedelta(seconds=10),
        )

        assert slack_message.get_active_update_task_id() is None

        slack_message.update_alert_groups_message(debounce=True)

        # Verify that apply_async was called with correct countdown
        mock_update_alert_group_slack_message.apply_async.assert_called_once_with(
            (slack_message.pk,),
            countdown=35,
            task_id=task_id,
        )

        # Verify the task ID in the cache is updated to new task_id
        slack_message.refresh_from_db()
        assert slack_message.get_active_update_task_id() == task_id

    @patch("apps.slack.models.slack_message.celery_uuid")
    @patch("apps.slack.models.slack_message.update_alert_group_slack_message")
    @pytest.mark.django_db
    def test_update_alert_groups_message_handles_minimum_countdown(
        self,
        mock_update_alert_group_slack_message,
        mock_celery_uuid,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_slack_channel,
        make_slack_message,
        make_alert_group,
    ):
        """
        Test that the countdown is at least 10 seconds when the debounce interval has passed.
        """
        task_id = "some-task-id"
        mock_celery_uuid.return_value = task_id

        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)

        slack_channel = make_slack_channel(slack_team_identity)
        slack_message = make_slack_message(
            slack_channel,
            alert_group=alert_group,
            last_updated=timezone.now()
            - timedelta(seconds=SlackMessage.ALERT_GROUP_UPDATE_DEBOUNCE_INTERVAL_SECONDS + 1),
        )

        assert slack_message.get_active_update_task_id() is None

        slack_message.update_alert_groups_message(debounce=True)

        # Verify that apply_async was called with correct countdown
        mock_update_alert_group_slack_message.apply_async.assert_called_once_with(
            (slack_message.pk,),
            # Since the time since last update exceeds the debounce interval, countdown should be 10
            countdown=10,
            task_id=task_id,
        )

        # Verify the task ID in the cache is updated to new task_id
        slack_message.refresh_from_db()
        assert slack_message.get_active_update_task_id() == task_id

    @patch("apps.slack.models.slack_message.celery_uuid")
    @patch("apps.slack.models.slack_message.update_alert_group_slack_message")
    @pytest.mark.django_db
    def test_update_alert_groups_message_debounce_false_schedules_immediately(
        self,
        mock_update_alert_group_slack_message,
        mock_celery_uuid,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_slack_channel,
        make_slack_message,
        make_alert_group,
    ):
        """
        Test that when debounce is False, the task is scheduled immediately with countdown=0,
        even if a task ID is set in the cache.
        """
        new_task_id = "new-task-id"
        mock_celery_uuid.return_value = new_task_id

        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        slack_channel = make_slack_channel(slack_team_identity)

        # Set up SlackMessage with existing task ID in the cache
        slack_message = make_slack_message(slack_channel, alert_group=alert_group)
        slack_message.set_active_update_task_id("existing-task-id")

        slack_message.update_alert_groups_message(debounce=False)

        # Verify that apply_async was called with countdown=0
        mock_update_alert_group_slack_message.apply_async.assert_called_once_with(
            (slack_message.pk,),
            countdown=0,
            task_id=new_task_id,
        )

        # Verify the task ID in the cache is updated to new task_id
        slack_message.refresh_from_db()
        assert slack_message.get_active_update_task_id() == new_task_id
