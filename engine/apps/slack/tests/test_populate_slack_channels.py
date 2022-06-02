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

    response = {
        "channels": (
            {"id": "C111111111", "name": "test1", "is_archived": False, "is_shared": False},
            {"id": "C222222222", "name": "test_changed_name", "is_archived": False, "is_shared": True},
            {"id": "C333333333", "name": "test3", "is_archived": False, "is_shared": True},
        )
    }
    with patch.object(SlackClientWithErrorHandling, "paginated_api_call", return_value=response):
        populate_slack_channels_for_team(slack_team_identity.pk)

    channels = slack_team_identity.cached_channels.all()

    expected_channel_ids = set(channel["id"] for channel in response["channels"])
    actual_channel_ids = set(channels.values_list("slack_id", flat=True))
    assert expected_channel_ids == actual_channel_ids

    assert not channels.filter(slack_id="C444444444").exists()

    second_channel = channels.get(slack_id="C222222222")
    assert second_channel.name == "test_changed_name"

    assert not channels.filter(last_populated__lte=yesterday).exists()
