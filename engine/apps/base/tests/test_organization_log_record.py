import pytest

from apps.base.models import OrganizationLogRecord


@pytest.mark.django_db
def test_organization_log_set_general_log_channel(
    make_organization_with_slack_team_identity, make_user_for_organization, make_slack_channel
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    user = make_user_for_organization(organization)

    slack_channel = make_slack_channel(slack_team_identity)
    organization.set_general_log_channel(slack_channel.slack_id, slack_channel.name, user)

    assert organization.log_records.filter(
        _labels=[OrganizationLogRecord.LABEL_SLACK, OrganizationLogRecord.LABEL_DEFAULT_CHANNEL]
    ).exists()
