from unittest.mock import patch

import pytest

from apps.schedules.tasks.shift_swaps import slack_messages as slack_msg_tasks


@patch("apps.slack.scenarios.shift_swap_requests.BaseShiftSwapRequestStep")
@pytest.mark.django_db
def test_create_shift_swap_request_message_not_found(MockBaseShiftSwapRequestStep):
    slack_msg_tasks.create_shift_swap_request_message("12345")

    MockBaseShiftSwapRequestStep.assert_not_called()
    MockBaseShiftSwapRequestStep.return_value.create_message.assert_not_called()


@patch("apps.slack.scenarios.shift_swap_requests.BaseShiftSwapRequestStep")
@pytest.mark.django_db
def test_create_shift_swap_request_message_no_configured_slack_channel_for_schedule(
    MockBaseShiftSwapRequestStep,
    shift_swap_request_setup,
):
    ssr, _, _ = shift_swap_request_setup()
    assert ssr.schedule.channel is None

    slack_msg_tasks.create_shift_swap_request_message(ssr.pk)

    MockBaseShiftSwapRequestStep.assert_not_called()
    MockBaseShiftSwapRequestStep.return_value.create_message.assert_not_called()


@patch("apps.slack.scenarios.shift_swap_requests.BaseShiftSwapRequestStep")
@pytest.mark.django_db
def test_create_shift_swap_request_message_post_message_to_channel_called(
    MockBaseShiftSwapRequestStep,
    shift_swap_request_setup,
    make_slack_message,
    make_slack_team_identity,
):
    slack_channel_id = "C1234ASDFJ"

    ssr, _, _ = shift_swap_request_setup()
    schedule = ssr.schedule
    organization = schedule.organization

    slack_message = make_slack_message(alert_group=None, organization=organization, slack_id="12345")
    slack_team_identity = make_slack_team_identity()

    MockBaseShiftSwapRequestStep.return_value.create_message.return_value = slack_message

    schedule.channel = slack_channel_id
    schedule.save()

    organization.slack_team_identity = slack_team_identity
    organization.save()

    slack_msg_tasks.create_shift_swap_request_message(ssr.pk)

    MockBaseShiftSwapRequestStep.assert_called_once_with(slack_team_identity, organization)
    MockBaseShiftSwapRequestStep.return_value.create_message.assert_called_once_with(ssr)

    ssr.refresh_from_db()
    assert ssr.slack_message.pk == str(slack_message.pk)


@patch("apps.slack.scenarios.shift_swap_requests.BaseShiftSwapRequestStep")
@pytest.mark.django_db
def test_update_shift_swap_request_message_not_found(MockBaseShiftSwapRequestStep):
    slack_msg_tasks.update_shift_swap_request_message("12345")

    MockBaseShiftSwapRequestStep.assert_not_called()
    MockBaseShiftSwapRequestStep.return_value.update_message.assert_not_called()


@patch("apps.slack.scenarios.shift_swap_requests.BaseShiftSwapRequestStep")
@pytest.mark.django_db
def test_update_shift_swap_request_message_no_configured_slack_channel_for_schedule(
    MockBaseShiftSwapRequestStep,
    shift_swap_request_setup,
):
    ssr, _, _ = shift_swap_request_setup()
    assert ssr.schedule.channel is None

    slack_msg_tasks.update_shift_swap_request_message(ssr.pk)

    MockBaseShiftSwapRequestStep.assert_not_called()
    MockBaseShiftSwapRequestStep.return_value.update_message.assert_not_called()


@patch("apps.slack.scenarios.shift_swap_requests.BaseShiftSwapRequestStep")
@pytest.mark.django_db
def test_update_shift_swap_request_message_post_message_to_channel_called(
    MockBaseShiftSwapRequestStep,
    shift_swap_request_setup,
    make_slack_team_identity,
):
    slack_channel_id = "C1234ASDFJ"

    ssr, _, _ = shift_swap_request_setup()
    schedule = ssr.schedule
    organization = schedule.organization

    slack_team_identity = make_slack_team_identity()

    schedule.channel = slack_channel_id
    schedule.save()

    organization.slack_team_identity = slack_team_identity
    organization.save()

    slack_msg_tasks.update_shift_swap_request_message(ssr.pk)

    MockBaseShiftSwapRequestStep.assert_called_once_with(slack_team_identity, organization)
    MockBaseShiftSwapRequestStep.return_value.update_message.assert_called_once_with(ssr)
