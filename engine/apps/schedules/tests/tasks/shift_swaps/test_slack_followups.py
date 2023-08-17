import datetime
from unittest.mock import ANY, patch

import pytest
from django.core.cache import cache
from django.utils import timezone

from apps.schedules.models import OnCallScheduleWeb, ShiftSwapRequest
from apps.schedules.tasks.shift_swaps import send_shift_swap_request_slack_followups
from apps.schedules.tasks.shift_swaps.slack_followups import (
    FOLLOWUP_WINDOW,
    _get_shift_swap_requests_in_followup_window,
    _mark_followup_sent,
    send_shift_swap_request_slack_followup,
)


@pytest.fixture
def shift_swap_request_test_setup(
    make_organization_with_slack_team_identity,
    make_user,
    make_schedule,
    make_slack_channel,
    make_slack_message,
    make_shift_swap_request,
):
    def _shift_swap_request_test_setup(swap_start=None, swap_end=None, **kwargs):
        organization, slack_team_identity = make_organization_with_slack_team_identity()
        user = make_user(organization=organization)

        slack_channel = make_slack_channel(slack_team_identity)
        slack_message = make_slack_message(alert_group=None, organization=organization, slack_id="12345")

        schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, channel=slack_channel.slack_id)

        if swap_start is None:
            swap_start = timezone.now() + timezone.timedelta(days=7)

        if swap_end is None:
            swap_end = swap_start + timezone.timedelta(days=1)

        shift_swap_request = make_shift_swap_request(
            schedule, user, swap_start=swap_start, swap_end=swap_end, slack_message=slack_message, **kwargs
        )
        return shift_swap_request

    return _shift_swap_request_test_setup


@patch.object(send_shift_swap_request_slack_followup, "delay")
@patch("apps.schedules.tasks.shift_swaps.slack_followups._mark_followup_sent")
@patch("apps.schedules.tasks.shift_swaps.slack_followups._has_followup_been_sent", return_value=False)
@pytest.mark.django_db
def test_send_shift_swap_request_followups(
    mock_has_followup_been_sent,
    mock_mark_followup_sent,
    mock_send_shift_swap_request_followup,
    shift_swap_request_test_setup,
):
    shift_swap_request = shift_swap_request_test_setup()

    with patch(
        "apps.schedules.tasks.shift_swaps.slack_followups._get_shift_swap_requests_in_followup_window",
        return_value=[shift_swap_request],
    ) as mock_get_shift_swap_requests_in_followup_window:
        send_shift_swap_request_slack_followups()

    mock_get_shift_swap_requests_in_followup_window.assert_called_once()
    mock_has_followup_been_sent.assert_called_once_with(shift_swap_request)
    mock_mark_followup_sent.assert_called_once_with(shift_swap_request)
    mock_send_shift_swap_request_followup.assert_called_once_with(shift_swap_request.pk)


@patch.object(send_shift_swap_request_slack_followup, "delay")
@patch("apps.schedules.tasks.shift_swaps.slack_followups._mark_followup_sent")
@patch("apps.schedules.tasks.shift_swaps.slack_followups._has_followup_been_sent", return_value=True)
@pytest.mark.django_db
def test_send_shift_swap_request_followups_already_sent(
    mock_has_followup_been_sent,
    mock_mark_followup_sent,
    mock_send_shift_swap_request_followup,
    shift_swap_request_test_setup,
):
    shift_swap_request = shift_swap_request_test_setup()

    with patch(
        "apps.schedules.tasks.shift_swaps.slack_followups._get_shift_swap_requests_in_followup_window",
        return_value=[shift_swap_request],
    ) as mock_get_shift_swap_requests_in_followup_window:
        send_shift_swap_request_slack_followups()

    mock_get_shift_swap_requests_in_followup_window.assert_called_once()
    mock_has_followup_been_sent.assert_called_once_with(shift_swap_request)
    mock_mark_followup_sent.assert_not_called()
    mock_send_shift_swap_request_followup.assert_not_called()


@pytest.mark.django_db
def test_get_shift_swap_requests_in_followup_window(shift_swap_request_test_setup):
    now = timezone.now()
    swap_start = now + timezone.timedelta(days=7)
    swap_end = swap_start + timezone.timedelta(days=1)
    shift_swap_request = shift_swap_request_test_setup(swap_start=swap_start, swap_end=swap_end)

    for offset in ShiftSwapRequest.FOLLOWUP_OFFSETS:
        # not yet
        assert (
            _get_shift_swap_requests_in_followup_window(swap_start - offset - datetime.timedelta(microseconds=1)) == []
        )

        # now
        assert _get_shift_swap_requests_in_followup_window(swap_start - offset) == [shift_swap_request]

        # in the window
        assert _get_shift_swap_requests_in_followup_window(swap_start - offset + FOLLOWUP_WINDOW // 2) == [
            shift_swap_request
        ]
        assert _get_shift_swap_requests_in_followup_window(swap_start - offset + FOLLOWUP_WINDOW) == [
            shift_swap_request
        ]

        # too late
        assert (
            _get_shift_swap_requests_in_followup_window(
                swap_start - offset + FOLLOWUP_WINDOW + datetime.timedelta(microseconds=1)
            )
            == []
        )


@pytest.mark.django_db
def test_get_shift_swap_requests_in_followup_not_open(shift_swap_request_test_setup, make_user):
    now = timezone.now()
    swap_start = now + timezone.timedelta(days=7)
    swap_end = swap_start + timezone.timedelta(days=1)

    # open
    ssr_open = shift_swap_request_test_setup(swap_start=swap_start, swap_end=swap_end)
    # taken
    shift_swap_request_test_setup(
        swap_start=swap_start, swap_end=swap_end, benefactor=make_user(organization=ssr_open.schedule.organization)
    )
    # deleted
    shift_swap_request_test_setup(swap_start=swap_start, swap_end=swap_end, deleted_at=now)
    # past due
    shift_swap_request_test_setup(swap_start=now - timezone.timedelta(days=1))

    assert _get_shift_swap_requests_in_followup_window(now) == [ssr_open]


def test_followup_offsets():
    for idx in range(1, len(ShiftSwapRequest.FOLLOWUP_OFFSETS)):
        assert ShiftSwapRequest.FOLLOWUP_OFFSETS[idx - 1] - ShiftSwapRequest.FOLLOWUP_OFFSETS[idx] > FOLLOWUP_WINDOW
        assert ShiftSwapRequest.FOLLOWUP_OFFSETS[idx] > FOLLOWUP_WINDOW


@patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call")
@pytest.mark.django_db
def test_send_shift_swap_request_followup(mock_slack_api_call, shift_swap_request_test_setup):
    shift_swap_request = shift_swap_request_test_setup()
    send_shift_swap_request_slack_followup(shift_swap_request.pk)

    mock_slack_api_call.assert_called_once_with(
        "chat.postMessage",
        channel=shift_swap_request.slack_message.channel_id,
        thread_ts=shift_swap_request.slack_message.slack_id,
        reply_broadcast=True,
        blocks=ANY,
    )


@pytest.mark.django_db
def test_mark_followup_sent(shift_swap_request_test_setup):
    shift_swap_request = shift_swap_request_test_setup()

    with patch.object(cache, "set") as mock_cache_set:
        _mark_followup_sent(shift_swap_request)
        assert mock_cache_set.call_args.kwargs["timeout"] == FOLLOWUP_WINDOW.total_seconds()
