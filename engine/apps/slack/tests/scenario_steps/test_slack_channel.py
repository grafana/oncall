from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.slack.models import SlackChannel, SlackMessage
from apps.slack.scenarios import slack_channel as slack_channel_scenarios


@pytest.mark.django_db
class TestSlackChannelCreatedOrRenamedEventStep:
    def test_process_scenario_channel_created(
        self,
        make_organization_and_user_with_slack_identities,
    ) -> None:
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()
        slack_channel_id = "C12345678"
        channel_name = "new-channel"
        payload = {
            "event": {
                "channel": {
                    "id": slack_channel_id,
                    "name": channel_name,
                }
            }
        }

        # Ensure the SlackChannel does not exist
        assert not SlackChannel.objects.filter(
            slack_id=slack_channel_id,
            slack_team_identity=slack_team_identity,
        ).exists()

        step = slack_channel_scenarios.SlackChannelCreatedOrRenamedEventStep(slack_team_identity, organization, user)
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

        # Now the SlackChannel should exist with correct data
        slack_channel = SlackChannel.objects.get(
            slack_id=slack_channel_id,
            slack_team_identity=slack_team_identity,
        )
        assert slack_channel.name == channel_name
        assert slack_channel.last_populated == timezone.now().date()

    def test_process_scenario_channel_renamed(
        self,
        make_organization_and_user_with_slack_identities,
        make_slack_channel,
    ) -> None:
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()
        slack_channel = make_slack_channel(slack_team_identity)
        slack_channel_id = slack_channel.slack_id
        new_name = "renamed-channel"
        payload = {
            "event": {
                "channel": {
                    "id": slack_channel_id,
                    "name": new_name,
                }
            }
        }

        step = slack_channel_scenarios.SlackChannelCreatedOrRenamedEventStep(slack_team_identity, organization, user)
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

        slack_channel.refresh_from_db()
        assert slack_channel.name == new_name
        assert slack_channel.last_populated == timezone.now().date()


@pytest.mark.django_db
class TestSlackChannelDeletedEventStep:
    def test_process_scenario_channel_deleted(
        self,
        make_organization_and_user_with_slack_identities,
        make_slack_channel,
        make_slack_message,
    ) -> None:
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()
        slack_channel = make_slack_channel(slack_team_identity)
        make_slack_message(slack_channel)
        slack_channel_id = slack_channel.slack_id

        # Ensure the SlackChannel exists
        assert SlackChannel.objects.filter(
            slack_id=slack_channel_id,
            slack_team_identity=slack_team_identity,
        ).exists()

        assert SlackMessage.objects.count() == 1

        step = slack_channel_scenarios.SlackChannelDeletedEventStep(slack_team_identity, organization, user)
        step.process_scenario(slack_user_identity, slack_team_identity, {"event": {"channel": slack_channel_id}})

        # Now the SlackChannel should not exist
        assert not SlackChannel.objects.filter(
            slack_id=slack_channel_id,
            slack_team_identity=slack_team_identity,
        ).exists()

        # Slack messages should be cascade deleted when their channel is deleted
        assert SlackMessage.objects.count() == 0

    def test_process_scenario_channel_does_not_exist(
        self,
        make_organization_and_user_with_slack_identities,
    ) -> None:
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()
        slack_channel_id = "C12345678"

        # Ensure the SlackChannel does not exist
        assert not SlackChannel.objects.filter(
            slack_id=slack_channel_id,
            slack_team_identity=slack_team_identity,
        ).exists()

        step = slack_channel_scenarios.SlackChannelDeletedEventStep(slack_team_identity, organization, user)
        # The step should not raise an exception even if the channel does not exist
        step.process_scenario(slack_user_identity, slack_team_identity, {"event": {"channel": slack_channel_id}})

        # Still, the SlackChannel does not exist
        assert not SlackChannel.objects.filter(
            slack_id=slack_channel_id,
            slack_team_identity=slack_team_identity,
        ).exists()


@pytest.mark.django_db
class TestSlackChannelArchivedEventStep:
    @patch("apps.slack.scenarios.slack_channel.clean_slack_channel_leftovers")
    def test_process_scenario(
        self,
        mock_clean_slack_channel_leftovers,
        make_organization_and_user_with_slack_identities,
        make_slack_channel,
    ) -> None:
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()
        slack_channel = make_slack_channel(slack_team_identity)
        slack_channel_id = slack_channel.slack_id

        assert slack_channel.is_archived is False

        step = slack_channel_scenarios.SlackChannelArchivedEventStep(slack_team_identity, organization, user)
        step.process_scenario(slack_user_identity, slack_team_identity, {"event": {"channel": slack_channel_id}})

        slack_channel.refresh_from_db()

        assert slack_channel.is_archived is True
        mock_clean_slack_channel_leftovers.apply_async.assert_called_once_with(
            (slack_team_identity.id, slack_channel_id)
        )


@pytest.mark.django_db
class TestSlackChannelUnarchivedEventStep:
    def test_process_scenario_channel_unarchived(
        self,
        make_organization_and_user_with_slack_identities,
        make_slack_channel,
    ) -> None:
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()
        slack_channel = make_slack_channel(slack_team_identity, is_archived=True)
        slack_channel_id = slack_channel.slack_id

        assert slack_channel.is_archived is True

        step = slack_channel_scenarios.SlackChannelUnarchivedEventStep(slack_team_identity, organization, user)
        step.process_scenario(slack_user_identity, slack_team_identity, {"event": {"channel": slack_channel_id}})

        slack_channel.refresh_from_db()
        assert slack_channel.is_archived is False

    def test_process_scenario_channel_already_unarchived(
        self,
        make_organization_and_user_with_slack_identities,
        make_slack_channel,
    ) -> None:
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()
        slack_channel = make_slack_channel(slack_team_identity, is_archived=False)
        slack_channel_id = slack_channel.slack_id

        assert slack_channel.is_archived is False

        step = slack_channel_scenarios.SlackChannelUnarchivedEventStep(slack_team_identity, organization, user)
        step.process_scenario(slack_user_identity, slack_team_identity, {"event": {"channel": slack_channel_id}})

        slack_channel.refresh_from_db()
        # Ensure that is_archived remains False
        assert slack_channel.is_archived is False
