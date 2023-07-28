from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.tasks import populate_slack_channels_for_team


@pytest.mark.django_db
def test_populate_slack_channels_for_team(make_organization_with_slack_team_identity, make_slack_channel):
    organization, slack_team_identity = make_organization_with_slack_team_identity()

    yesterday = (timezone.now() - timezone.timedelta(days=1)).date()
    _ = tuple(
        make_slack_channel(
            slack_team_identity=slack_team_identity, slack_id=slack_id, name=name, last_populated=yesterday
        )
        for slack_id, name in (
            ("C111111111", "test1"),
            ("C222222222", "test2"),
            ("C444444444", "test4"),
        )
    )

    response, cursor, rate_limited = (
        {
            "channels": (
                {"id": "C111111111", "name": "test1", "is_archived": False, "is_shared": False},
                {"id": "C222222222", "name": "test_changed_name", "is_archived": False, "is_shared": True},
                {"id": "C333333333", "name": "test3", "is_archived": False, "is_shared": True},
            )
        },
        None,
        False,
    )

    with patch.object(
        SlackClientWithErrorHandling, "paginated_api_call_with_ratelimit", return_value=(response, cursor, rate_limited)
    ):
        populate_slack_channels_for_team(slack_team_identity.pk)

    channels = slack_team_identity.cached_channels.all()

    expected_channel_ids = set(channel["id"] for channel in response["channels"])
    actual_channel_ids = set(channels.values_list("slack_id", flat=True))
    assert expected_channel_ids == actual_channel_ids

    assert not channels.filter(slack_id="C444444444").exists()

    second_channel = channels.get(slack_id="C222222222")
    assert second_channel.name == "test_changed_name"

    assert not channels.filter(last_populated__lte=yesterday).exists()


@patch("apps.slack.tasks.start_populate_slack_channels_for_team")
@pytest.mark.django_db
def test_populate_slack_channels_for_team_ratelimit(
    mocked_start_populate_slack_channels_for_team,
    make_organization_with_slack_team_identity,
    make_slack_channel,
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()

    yesterday = (timezone.now() - timezone.timedelta(days=1)).date()
    today = timezone.now().date()

    _ = tuple(
        make_slack_channel(
            slack_team_identity=slack_team_identity, slack_id=slack_id, name=name, last_populated=yesterday
        )
        for slack_id, name in (
            ("C111111111", "test1"),
            ("C222222222", "test2"),
            ("C444444444", "test4"),
        )
    )
    # first response with rate limit error
    response_1, cursor_1, rate_limited_1 = (
        {"channels": ({"id": "C111111111", "name": "test1", "is_archived": False, "is_shared": False},)},
        "TESTCURSOR1",
        True,
    )

    # second response with rate limit error
    response_2, cursor_2, rate_limited_2 = (
        {
            "channels": (
                {"id": "C111111111", "name": "test1", "is_archived": False, "is_shared": False},
                {"id": "C222222222", "name": "test_changed_name", "is_archived": False, "is_shared": True},
            )
        },
        "TESTCURSOR2",
        True,
    )

    # third response without rate limit error
    response_3, cursor_3, rate_limited_3 = (
        {
            "channels": (
                {"id": "C222222222", "name": "test_changed_name", "is_archived": False, "is_shared": True},
                {"id": "C333333333", "name": "test3", "is_archived": False, "is_shared": True},
            )
        },
        "",
        False,
    )
    # these channels should exist after finishing populate_slack_channels_for_team
    expected_channel_ids = {"C111111111", "C222222222", "C333333333"}

    with patch.object(
        SlackClientWithErrorHandling,
        "paginated_api_call_with_ratelimit",
        return_value=(response_1, cursor_1, rate_limited_1),
    ):
        populate_slack_channels_for_team(slack_team_identity.pk)

    # expected only one channel to update and no channel to delete
    # start_populate_slack_channels_for_team should be called
    channels = slack_team_identity.cached_channels.all()
    channel_1 = channels.get(slack_id="C111111111")
    assert channel_1.last_populated == today

    channel_2 = channels.get(slack_id="C222222222")
    assert channel_2.last_populated == yesterday

    assert channels.filter(slack_id="C444444444").exists()

    assert mocked_start_populate_slack_channels_for_team.called
    assert mocked_start_populate_slack_channels_for_team.call_count == 1

    with patch.object(
        SlackClientWithErrorHandling,
        "paginated_api_call_with_ratelimit",
        return_value=(response_2, cursor_2, rate_limited_2),
    ):
        populate_slack_channels_for_team(slack_team_identity.pk, cursor_1)

    # expected another one channel to update and no channel to delete
    # start_populate_slack_channels_for_team should be called
    channels = slack_team_identity.cached_channels.all()

    channel_2 = channels.get(slack_id="C222222222")
    assert channel_2.last_populated == today
    assert channel_2.name == "test_changed_name"

    assert not channels.filter(slack_id="C333333333").exists()
    assert channels.filter(slack_id="C444444444").exists()

    assert mocked_start_populate_slack_channels_for_team.called
    assert mocked_start_populate_slack_channels_for_team.call_count == 2

    with patch.object(
        SlackClientWithErrorHandling,
        "paginated_api_call_with_ratelimit",
        return_value=(response_3, cursor_3, rate_limited_3),
    ):
        populate_slack_channels_for_team(slack_team_identity.pk, cursor_1)

    # expected one new channel and one deleted channel. List of channel ids in response and in db should be the same
    # start_populate_slack_channels_for_team should NOT be called
    channels = slack_team_identity.cached_channels.all()

    actual_channel_ids = set(channels.values_list("slack_id", flat=True))
    assert actual_channel_ids == expected_channel_ids

    assert not channels.filter(slack_id="C444444444").exists()

    channel_2 = channels.get(slack_id="C222222222")
    assert channel_2.name == "test_changed_name"

    assert not channels.filter(last_populated__lte=yesterday).exists()
    assert mocked_start_populate_slack_channels_for_team.call_count == 2
