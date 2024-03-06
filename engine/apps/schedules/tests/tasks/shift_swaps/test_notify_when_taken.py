from unittest.mock import patch

import pytest

from apps.schedules.tasks.shift_swaps import notify_beneficiary_about_taken_shift_swap_request


@patch(
    "apps.schedules.tasks.shift_swaps.notify_when_taken.notify_beneficiary_about_taken_shift_swap_request_via_push_notification"
)
@patch("apps.slack.scenarios.shift_swap_requests.AcceptShiftSwapRequestStep")
@pytest.mark.django_db
def test_notify_beneficiary_about_taken_shift_swap_request_not_found(
    MockAcceptShiftSwapRequestStep,
    mock_notify_beneficiary_about_taken_shift_swap_request_via_push_notification,
):
    notify_beneficiary_about_taken_shift_swap_request("12345")

    MockAcceptShiftSwapRequestStep.assert_not_called()
    MockAcceptShiftSwapRequestStep.return_value.post_request_taken_message_to_thread.assert_not_called()

    mock_notify_beneficiary_about_taken_shift_swap_request_via_push_notification.apply_async.assert_not_called()


@patch(
    "apps.schedules.tasks.shift_swaps.notify_when_taken.notify_beneficiary_about_taken_shift_swap_request_via_push_notification"
)
@patch("apps.slack.scenarios.shift_swap_requests.AcceptShiftSwapRequestStep")
@pytest.mark.django_db
def test_notify_beneficiary_about_taken_shift_swap_request_no_configured_slack_channel_for_schedule(
    MockAcceptShiftSwapRequestStep,
    mock_notify_beneficiary_about_taken_shift_swap_request_via_push_notification,
    shift_swap_request_setup,
):
    ssr, _, _ = shift_swap_request_setup()
    assert ssr.schedule.channel is None

    notify_beneficiary_about_taken_shift_swap_request(ssr.pk)

    mock_notify_beneficiary_about_taken_shift_swap_request_via_push_notification.apply_async.assert_called_once_with(
        (ssr.pk,)
    )

    MockAcceptShiftSwapRequestStep.assert_not_called()
    MockAcceptShiftSwapRequestStep.return_value.post_request_taken_message_to_thread.assert_not_called()


@patch(
    "apps.schedules.tasks.shift_swaps.notify_when_taken.notify_beneficiary_about_taken_shift_swap_request_via_push_notification"
)
@patch("apps.slack.scenarios.shift_swap_requests.AcceptShiftSwapRequestStep")
@pytest.mark.django_db
def test_notify_beneficiary_about_taken_shift_swap_request_post_message_to_channel_called(
    MockAcceptShiftSwapRequestStep,
    mock_notify_beneficiary_about_taken_shift_swap_request_via_push_notification,
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

    notify_beneficiary_about_taken_shift_swap_request(ssr.pk)

    MockAcceptShiftSwapRequestStep.assert_called_once_with(slack_team_identity, organization)
    MockAcceptShiftSwapRequestStep.return_value.post_request_taken_message_to_thread.assert_called_once_with(ssr)

    mock_notify_beneficiary_about_taken_shift_swap_request_via_push_notification.apply_async.assert_called_once_with(
        (ssr.pk,)
    )
