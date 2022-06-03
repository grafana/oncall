import pytest

from apps.schedules.ical_utils import users_in_ical


@pytest.mark.skip(reason="For now ical searching works only by username")
@pytest.mark.django_db
def test_search_user_by_profile_display_name(
    make_organization_with_slack_team_identity,
    make_user_with_slack_user_identity,
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    make_user_with_slack_user_identity(slack_team_identity, profile_display_name="Alex")

    assert len(users_in_ical(["Alex"], organization)) == 1


@pytest.mark.django_db
def test_search_user_by_username(
    make_organization,
    make_user,
):
    organization_1 = make_organization()
    organization_2 = make_organization()
    test_username = "Alex"
    make_user(organization=organization_1, username=test_username)

    assert len(users_in_ical([test_username], organization_1)) == 1
    assert len(users_in_ical([test_username], organization_2)) == 0


@pytest.mark.skip(reason="For now ical searching works only by username")
@pytest.mark.django_db
def test_search_by_slack_user_identity_for_different_organizations(
    make_organization_with_slack_team_identity,
    make_user_with_slack_user_identity,
    make_organization,
):
    organization_1, slack_team_identity_1 = make_organization_with_slack_team_identity()
    organization_2 = make_organization(slack_team_identity=slack_team_identity_1)
    test_profile_display_name = "Alex"
    make_user_with_slack_user_identity(
        slack_team_identity_1, organization=organization_1, profile_display_name=test_profile_display_name
    )

    assert len(users_in_ical([test_profile_display_name], organization_1)) == 1
    assert len(users_in_ical([test_profile_display_name], organization_2)) == 0


@pytest.mark.skip(reason="For now ical searching works only by username")
@pytest.mark.django_db
def test_search_with_deleted_slack_user_identity_in_another_team(
    make_organization_with_slack_team_identity,
    make_user_with_slack_user_identity,
):
    organization_1, slack_team_identity_1 = make_organization_with_slack_team_identity()
    organization_2, slack_team_identity_2 = make_organization_with_slack_team_identity()
    make_user_with_slack_user_identity(
        slack_team_identity_1, organization=organization_1, profile_display_name="Alex", deleted=False
    )
    make_user_with_slack_user_identity(
        slack_team_identity_2, organization=organization_2, profile_display_name="Bob", deleted=True
    )

    assert len(users_in_ical(["Alex"], organization_1)) == 1


@pytest.mark.skip(reason="For now ical searching works only by username")
@pytest.mark.django_db
def test_search_with_deleted_slack_user_identity(
    make_team_and_user,
    make_team_for_user,
    make_slack_team_identity_for_team,
    make_user_with_slack_user_identity,
):
    amixr_team_1, amixr_user = make_team_and_user()
    slack_team_identity_1 = make_slack_team_identity_for_team(amixr_team_1)
    make_user_with_slack_user_identity(amixr_user, slack_team_identity_1, profile_display_name="Alex", deleted=True)

    assert len(users_in_ical(["Alex"], amixr_team_1)) == 0


@pytest.mark.skip(reason="For now ical searching works only by username")
@pytest.mark.django_db
def test_search_users_with_and_without_slack_user_identity(
    make_team,
    make_user,
    make_slack_team_identity_for_team,
    make_user_with_slack_user_identity,
):
    amixr_team = make_team()
    slack_team_identity = make_slack_team_identity_for_team(amixr_team)

    amixr_user_with_sui = make_user()
    # make_role(amixr_user_with_sui, amixr_team, username="Alex")
    make_user_with_slack_user_identity(amixr_user_with_sui, slack_team_identity, profile_display_name="Alex")

    # amixr_user_without_sui = make_user()
    # make_role(amixr_user_without_sui, amixr_team, username="Bob")

    assert len(users_in_ical(["Bob"], amixr_team)) == 1
    assert len(users_in_ical(["Alex"], amixr_team)) == 1
    assert len(users_in_ical(["Alex", "Bob"], amixr_team)) == 2
