from unittest.mock import Mock, patch

import pytest

from apps.alerts.models import ResolutionNoteSlackMessage
from apps.slack.client import SlackAPIException
from apps.slack.scenarios.slack_channel_integration import SlackChannelMessageEventStep


@pytest.mark.django_db
class TestSlackChannelMessageEventStep:
    @patch.object(SlackChannelMessageEventStep, "save_thread_message_for_resolution_note")
    @patch.object(SlackChannelMessageEventStep, "delete_thread_message_from_resolution_note")
    @pytest.mark.parametrize(
        "payload,save_called,delete_called",
        [
            (
                {
                    # does not have thread_ts attribute or subtype
                    "event": {},
                },
                False,
                False,
            ),
            (
                {
                    # has thread_ts attribute but has subtype attribute that is not MESSAGE_CHANGED
                    "event": {
                        "thread_ts": "foo",
                        "subtype": "bar",
                    },
                },
                False,
                False,
            ),
            (
                {
                    # has thread_ts attribute but not subtype attribute
                    "event": {
                        "thread_ts": "foo",
                    },
                },
                True,
                False,
            ),
            # MESSAGE_CHANGED event.subtype scenarios
            (
                {
                    "event": {
                        "subtype": "message_changed",
                        "message": {
                            "subtype": "bar",
                            "thread_ts": "hello",
                        },
                    },
                },
                False,
                False,
            ),
            (
                {
                    "event": {
                        "subtype": "message_changed",
                        "message": {
                            "subtype": "bar",
                        },
                    },
                },
                False,
                False,
            ),
            (
                {
                    "event": {
                        "subtype": "potato",
                        "message": {
                            "thread_ts": "bar",
                        },
                    },
                },
                False,
                False,
            ),
            (
                {
                    "event": {
                        "subtype": "message_changed",
                        "message": {
                            "thread_ts": "bar",
                        },
                    },
                },
                True,
                False,
            ),
            (
                {
                    "event": {
                        "subtype": "message_deleted",
                        "previous_message": {},
                    },
                },
                False,
                False,
            ),
            (
                {
                    "event": {
                        "subtype": "message_deleted",
                        "previous_message": {},
                    },
                },
                False,
                False,
            ),
            (
                {
                    "event": {
                        "subtype": "potato",
                        "previous_message": {
                            "thread_ts": "bar",
                        },
                    },
                },
                False,
                False,
            ),
            (
                {
                    "event": {
                        "subtype": "message_deleted",
                        "previous_message": {
                            "thread_ts": "bar",
                        },
                    },
                },
                False,
                True,
            ),
        ],
    )
    def test_process_scenario(
        self,
        mock_delete_thread_message_from_resolution_note,
        mock_save_thread_message_for_resolution_note,
        make_organization_and_user_with_slack_identities,
        payload,
        save_called,
        delete_called,
    ) -> None:
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()

        step = SlackChannelMessageEventStep(slack_team_identity, organization, user)
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

        if save_called:
            mock_save_thread_message_for_resolution_note.assert_called_once_with(slack_user_identity, payload)
        else:
            mock_save_thread_message_for_resolution_note.assert_not_called()

        if delete_called:
            mock_delete_thread_message_from_resolution_note.assert_called_once_with(slack_user_identity, payload)
        else:
            mock_delete_thread_message_from_resolution_note.assert_not_called()

    @patch("apps.alerts.models.ResolutionNoteSlackMessage")
    def test_save_thread_message_for_resolution_note_no_slack_user_identity(
        self, MockResolutionNoteSlackMessage, make_organization_and_user_with_slack_identities
    ) -> None:
        organization, user, slack_team_identity, _ = make_organization_and_user_with_slack_identities()

        step = SlackChannelMessageEventStep(slack_team_identity, organization, user)
        step._slack_client = Mock()

        step.save_thread_message_for_resolution_note(None, {})

        step._slack_client.api_call.assert_not_called()
        MockResolutionNoteSlackMessage.objects.get_or_create.assert_not_called()

    @patch("apps.alerts.models.ResolutionNoteSlackMessage")
    def test_save_thread_message_for_resolution_note_no_slack_message(
        self, MockResolutionNoteSlackMessage, make_organization_and_user_with_slack_identities
    ) -> None:
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()

        step = SlackChannelMessageEventStep(slack_team_identity, organization, user)
        step._slack_client = Mock()

        payload = {
            "event": {
                "channel": "potato",
                "ts": 88945.4849,
                "thread_ts": 16789.123,
                "text": "hello",
            },
        }

        step.save_thread_message_for_resolution_note(slack_user_identity, payload)

        step._slack_client.api_call.assert_not_called()
        MockResolutionNoteSlackMessage.objects.get_or_create.assert_not_called()

    @patch("apps.alerts.models.ResolutionNoteSlackMessage")
    def test_save_thread_message_for_resolution_note_really_long_text(
        self,
        MockResolutionNoteSlackMessage,
        make_organization_and_user_with_slack_identities,
        make_alert_receive_channel,
        make_alert_group,
        make_slack_message,
    ) -> None:
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()
        integration = make_alert_receive_channel(organization)
        alert_group = make_alert_group(integration)

        channel = "potato"
        ts = 88945.4849
        thread_ts = 16789.123

        make_slack_message(alert_group, slack_id=thread_ts, channel_id=channel)

        mock_permalink = "http://example.com"

        step = SlackChannelMessageEventStep(slack_team_identity, organization, user)
        step._slack_client = Mock()
        step._slack_client.chat_getPermalink.return_value = {"permalink": mock_permalink}

        payload = {
            "event": {
                "channel": channel,
                "ts": ts,
                "thread_ts": thread_ts,
                "text": "h" * 2901,
            },
        }

        step.save_thread_message_for_resolution_note(slack_user_identity, payload)

        step._slack_client.chat_getPermalink.assert_called_once_with(
            channel=payload["event"]["channel"],
            message_ts=payload["event"]["ts"],
        )
        step._slack_client.chat_postEphemeral.assert_called_once_with(
            channel=payload["event"]["channel"],
            user=slack_user_identity.slack_id,
            text=":warning: Unable to show the <{}|message> in Resolution Note: the message is too long ({}). "
            "Max length - 2900 symbols.".format(mock_permalink, len(payload["event"]["text"])),
        )
        MockResolutionNoteSlackMessage.objects.get_or_create.assert_not_called()

    @patch("apps.alerts.models.ResolutionNoteSlackMessage")
    def test_save_thread_message_for_resolution_note_api_errors(
        self,
        MockResolutionNoteSlackMessage,
        make_organization_and_user_with_slack_identities,
        make_alert_receive_channel,
        make_alert_group,
        make_slack_message,
    ) -> None:
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()
        integration = make_alert_receive_channel(organization)
        alert_group = make_alert_group(integration)

        channel = "potato"
        ts = 88945.4849
        thread_ts = 16789.123

        make_slack_message(alert_group, slack_id=thread_ts, channel_id=channel)

        step = SlackChannelMessageEventStep(slack_team_identity, organization, user)
        step._slack_client = Mock()
        step._slack_client.chat_getPermalink.side_effect = [
            SlackAPIException("error!", response={"ok": False, "error": "message_not_found"})
        ]

        payload = {
            "event": {
                "channel": channel,
                "ts": ts,
                "thread_ts": thread_ts,
                "text": "h" * 2901,
            },
        }

        step.save_thread_message_for_resolution_note(slack_user_identity, payload)

        step._slack_client.chat_getPermalink.assert_called_once_with(
            channel=payload["event"]["channel"],
            message_ts=payload["event"]["ts"],
        )
        MockResolutionNoteSlackMessage.objects.get_or_create.assert_not_called()

    @pytest.mark.parametrize("resolution_note_slack_message_already_exists", [True, False])
    def test_save_thread_message_for_resolution_note(
        self,
        make_organization_and_user_with_slack_identities,
        make_alert_receive_channel,
        make_alert_group,
        make_slack_message,
        make_resolution_note_slack_message,
        resolution_note_slack_message_already_exists,
    ) -> None:
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()
        integration = make_alert_receive_channel(organization)
        alert_group = make_alert_group(integration)

        original_text = "original text"
        new_text = "new text"

        channel = "potato"
        ts = 88945.4849
        thread_ts = 16789.123

        make_slack_message(alert_group, slack_id=thread_ts, channel_id=channel)

        resolution_note_slack_message = None
        if resolution_note_slack_message_already_exists:
            resolution_note_slack_message = make_resolution_note_slack_message(
                alert_group, user, user, ts=ts, thread_ts=thread_ts, text=original_text
            )

        mock_permalink = "http://example.com"

        step = SlackChannelMessageEventStep(slack_team_identity, organization, user)
        step._slack_client = Mock()
        step._slack_client.chat_getPermalink.side_effect = [{"permalink": mock_permalink}, None]

        payload = {
            "event": {
                "channel": channel,
                "ts": ts,
                "thread_ts": thread_ts,
                "text": new_text,
            },
        }

        step.save_thread_message_for_resolution_note(slack_user_identity, payload)

        step._slack_client.chat_getPermalink.assert_called_once_with(
            channel=payload["event"]["channel"],
            message_ts=payload["event"]["ts"],
        )

        if resolution_note_slack_message_already_exists:
            resolution_note_slack_message.refresh_from_db()
            resolution_note_slack_message.text = new_text
        else:
            assert (
                ResolutionNoteSlackMessage.objects.filter(
                    ts=ts,
                    thread_ts=thread_ts,
                    alert_group=alert_group,
                ).count()
                == 1
            )

    @patch("apps.alerts.models.ResolutionNoteSlackMessage")
    def test_delete_thread_message_from_resolution_note_no_slack_user_identity(
        self, MockResolutionNoteSlackMessage, make_organization_and_user_with_slack_identities
    ) -> None:
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()

        step = SlackChannelMessageEventStep(slack_team_identity, organization, user)
        step.delete_thread_message_from_resolution_note(None, {})

        MockResolutionNoteSlackMessage.objects.get.assert_not_called()

    def test_delete_thread_message_from_resolution_note_no_message_found(
        self, make_organization_and_user_with_slack_identities
    ) -> None:
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()

        channel = "potato"
        ts = 88945.4849
        thread_ts = 16789.123

        payload = {
            "event": {
                "channel": channel,
                "previous_message": {
                    "ts": ts,
                    "thread_ts": thread_ts,
                },
            },
        }

        step = SlackChannelMessageEventStep(slack_team_identity, organization, user)
        step.alert_group_slack_service = Mock()

        step.delete_thread_message_from_resolution_note(slack_user_identity, payload)

        step.alert_group_slack_service.assert_not_called()

    def test_delete_thread_message_from_resolution_note(
        self,
        make_organization_and_user_with_slack_identities,
        make_alert_receive_channel,
        make_alert_group,
        make_resolution_note_slack_message,
    ) -> None:
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()
        integration = make_alert_receive_channel(organization)
        alert_group = make_alert_group(integration)

        channel = "potato"
        ts = 88945.4849
        thread_ts = 16789.123

        payload = {
            "event": {
                "channel": channel,
                "previous_message": {
                    "ts": ts,
                    "thread_ts": thread_ts,
                },
            },
        }

        make_resolution_note_slack_message(
            alert_group, user, user, ts=ts, thread_ts=thread_ts, slack_channel_id=channel
        )

        step = SlackChannelMessageEventStep(slack_team_identity, organization, user)
        step.alert_group_slack_service = Mock()

        step.delete_thread_message_from_resolution_note(slack_user_identity, payload)

        step.alert_group_slack_service.update_alert_group_slack_message.assert_called_once_with(alert_group)
        assert (
            ResolutionNoteSlackMessage.objects.filter(
                ts=ts,
                thread_ts=thread_ts,
                slack_channel_id=channel,
            ).count()
            == 0
        )

    def test_slack_message_has_no_alert_group(
        self,
        make_organization_and_user_with_slack_identities,
        make_slack_message,
    ) -> None:
        """Thread messages for SlackMessage instances without alert_group set (e.g., SSR Slack messages)"""
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()

        channel = "potato"
        ts = 88945.4849
        thread_ts = 16789.123

        payload = {
            "event": {
                "channel": channel,
                "ts": ts,
                "thread_ts": thread_ts,
                "text": "hello",
            },
        }

        make_slack_message(alert_group=None, organization=organization, slack_id=thread_ts, channel_id=channel)

        step = SlackChannelMessageEventStep(slack_team_identity, organization, user)
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

        assert not ResolutionNoteSlackMessage.objects.exists()
