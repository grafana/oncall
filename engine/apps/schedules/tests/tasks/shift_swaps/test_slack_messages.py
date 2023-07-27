import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.schedules.models import OnCallScheduleWeb
from apps.schedules.tasks.shift_swaps import slack_messages as slack_msg_tasks


@pytest.fixture
def ssr_setup(make_schedule, make_organization_and_user, make_user_for_organization, make_shift_swap_request):
    def _ssr_setup():
        organization, beneficiary = make_organization_and_user()
        benefactor = make_user_for_organization(organization)

        schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        two_days_from_now = tomorrow + datetime.timedelta(days=1)

        ssr = make_shift_swap_request(schedule, beneficiary, swap_start=tomorrow, swap_end=two_days_from_now)

        return ssr, beneficiary, benefactor

    return _ssr_setup


@patch("apps.schedules.tasks.shift_swaps.slack_messages.post_message_to_channel")
@pytest.mark.django_db
def test_post_shift_swap_request_creation_message_not_found(mock_post_message_to_channel):
    slack_msg_tasks.post_shift_swap_request_creation_message("12345")
    mock_post_message_to_channel.assert_not_called()


@patch("apps.schedules.tasks.shift_swaps.slack_messages.post_message_to_channel")
@pytest.mark.django_db
def test_post_shift_swap_request_creation_message_no_configured_slack_channel_for_schedule(
    mock_post_message_to_channel,
    ssr_setup,
):
    ssr, _, _ = ssr_setup()
    assert ssr.schedule.channel is None

    slack_msg_tasks.post_shift_swap_request_creation_message(ssr.pk)

    mock_post_message_to_channel.assert_not_called()


@patch("apps.schedules.tasks.shift_swaps.slack_messages.post_message_to_channel")
@pytest.mark.django_db
def test_post_shift_swap_request_creation_message_post_message_to_channel_called(
    mock_post_message_to_channel, ssr_setup
):
    text = "joey testing"
    slack_channel_id = "C1234ASDFJ"

    ssr, _, _ = ssr_setup()

    schedule = ssr.schedule
    schedule.channel = slack_channel_id
    schedule.save()

    slack_msg_tasks.post_shift_swap_request_creation_message(ssr.pk)

    mock_post_message_to_channel.assert_called_once_with(schedule.organization, slack_channel_id, text)
