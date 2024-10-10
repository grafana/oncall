import datetime

import pytest
from django.utils import timezone

from apps.api import permissions
from apps.google import constants as google_constants
from apps.google.models import GoogleOAuth2User
from apps.user_management.models import User


@pytest.mark.django_db
def test_self_or_has_user_settings_admin_permission(make_organization, make_user_for_organization):
    # RBAC not enabled for org
    organization = make_organization(is_rbac_permissions_enabled=False)
    admin = make_user_for_organization(organization)
    second_admin = make_user_for_organization(organization)
    editor = make_user_for_organization(organization, role=permissions.LegacyAccessControlRole.EDITOR)

    another_organization = make_organization(is_rbac_permissions_enabled=False)
    admin_from_another_organization = make_user_for_organization(another_organization)

    assert organization.is_rbac_permissions_enabled is False
    assert another_organization.is_rbac_permissions_enabled is False

    assert admin.self_or_has_user_settings_admin_permission(admin, organization) is True
    assert admin.self_or_has_user_settings_admin_permission(editor, organization) is False
    assert admin.self_or_has_user_settings_admin_permission(second_admin, organization) is True

    assert admin.self_or_has_user_settings_admin_permission(admin_from_another_organization, organization) is False

    assert editor.self_or_has_user_settings_admin_permission(editor, organization) is True
    assert editor.self_or_has_user_settings_admin_permission(admin, organization) is True

    # RBAC enabled org
    organization_with_rbac = make_organization(is_rbac_permissions_enabled=True)
    user_with_perms = make_user_for_organization(
        organization_with_rbac,
        role=permissions.LegacyAccessControlRole.NONE,
        permissions=permissions.GrafanaAPIPermissions.construct_permissions(
            [permissions.RBACPermission.Permissions.USER_SETTINGS_ADMIN.value]
        ),
    )
    user_without_perms = make_user_for_organization(
        organization_with_rbac,
        role=permissions.LegacyAccessControlRole.NONE,
        permissions=[],
    )

    assert organization_with_rbac.is_rbac_permissions_enabled is True

    # true because self
    assert user_with_perms.self_or_has_user_settings_admin_permission(user_with_perms, organization_with_rbac) is True
    assert (
        user_without_perms.self_or_has_user_settings_admin_permission(user_without_perms, organization_with_rbac)
        is True
    )

    # true because user_with_perms has proper admin RBAC permission
    assert (
        user_without_perms.self_or_has_user_settings_admin_permission(user_with_perms, organization_with_rbac) is True
    )

    # false because user_without_perms does not have proper admin RBAC permission
    assert (
        user_with_perms.self_or_has_user_settings_admin_permission(user_without_perms, organization_with_rbac) is False
    )


@pytest.mark.django_db
def test_is_admin(make_organization, make_user_for_organization):
    # RBAC not enabled for org
    organization = make_organization(is_rbac_permissions_enabled=False)
    admin = make_user_for_organization(organization, role=permissions.LegacyAccessControlRole.ADMIN)
    editor = make_user_for_organization(organization, role=permissions.LegacyAccessControlRole.EDITOR)

    assert organization.is_rbac_permissions_enabled is False

    assert admin.is_admin is True
    assert editor.is_admin is False

    # RBAC enabled org
    organization_with_rbac = make_organization(is_rbac_permissions_enabled=True)
    user_with_perms = make_user_for_organization(
        organization_with_rbac,
        role=permissions.LegacyAccessControlRole.NONE,
        permissions=permissions.GrafanaAPIPermissions.construct_permissions(
            [permissions.RBACPermission.Permissions.ADMIN.value]
        ),
    )
    user_without_perms = make_user_for_organization(
        organization_with_rbac,
        role=permissions.LegacyAccessControlRole.NONE,
        permissions=[],
    )

    assert organization_with_rbac.is_rbac_permissions_enabled is True

    assert user_with_perms.is_admin is True
    assert user_without_perms.is_admin is False


@pytest.mark.django_db
def test_lower_email_filter(make_organization, make_user_for_organization):
    organization = make_organization()
    user = make_user_for_organization(organization, email="TestingUser@test.com")
    make_user_for_organization(organization, email="testing_user@test.com")

    assert User.objects.get(email__lower="testinguser@test.com") == user
    assert User.objects.filter(email__lower__in=["testinguser@test.com"]).get() == user


@pytest.mark.django_db
def test_is_in_working_hours(make_organization, make_user_for_organization):
    organization = make_organization()
    user = make_user_for_organization(organization, _timezone="Europe/London")

    _7_59_utc = timezone.datetime(2023, 8, 1, 7, 59, 59, tzinfo=datetime.timezone.utc)
    _8_utc = timezone.datetime(2023, 8, 1, 8, 0, 0, tzinfo=datetime.timezone.utc)
    _17_utc = timezone.datetime(2023, 8, 1, 16, 0, 0, tzinfo=datetime.timezone.utc)
    _17_01_utc = timezone.datetime(2023, 8, 1, 16, 0, 1, tzinfo=datetime.timezone.utc)

    assert user.is_in_working_hours(_7_59_utc) is False
    assert user.is_in_working_hours(_8_utc) is True
    assert user.is_in_working_hours(_17_utc) is True
    assert user.is_in_working_hours(_17_01_utc) is False


@pytest.mark.django_db
def test_is_in_working_hours_next_day(make_organization, make_user_for_organization):
    organization = make_organization()
    user = make_user_for_organization(
        organization,
        working_hours={
            "tuesday": [{"start": "17:00:00", "end": "18:00:00"}],
            "wednesday": [{"start": "01:00:00", "end": "02:00:00"}],
        },
    )

    _8_59_utc = timezone.datetime(2023, 8, 1, 8, 59, 59, tzinfo=datetime.timezone.utc)  # 4:59pm on Tuesday in Singapore
    _9_utc = timezone.datetime(2023, 8, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)  # 5pm on Tuesday in Singapore
    _10_utc = timezone.datetime(2023, 8, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)  # 6pm on Tuesday in Singapore
    _10_01_utc = timezone.datetime(2023, 8, 1, 10, 0, 1, tzinfo=datetime.timezone.utc)  # 6:01pm on Tuesday in Singapore

    _16_59_utc = timezone.datetime(
        2023, 8, 1, 16, 59, 0, tzinfo=datetime.timezone.utc
    )  # 00:59am on Wednesday in Singapore
    _17_utc = timezone.datetime(2023, 8, 1, 17, 0, 0, tzinfo=datetime.timezone.utc)  # 1am on Wednesday in Singapore
    _18_utc = timezone.datetime(2023, 8, 1, 18, 0, 0, tzinfo=datetime.timezone.utc)  # 2am on Wednesday in Singapore
    _18_01_utc = timezone.datetime(
        2023, 8, 1, 18, 0, 1, tzinfo=datetime.timezone.utc
    )  # 2:01am on Wednesday in Singapore

    tz = "Asia/Singapore"
    assert user.is_in_working_hours(_8_59_utc, tz=tz) is False
    assert user.is_in_working_hours(_9_utc, tz=tz) is True
    assert user.is_in_working_hours(_10_utc, tz=tz) is True
    assert user.is_in_working_hours(_10_01_utc, tz=tz) is False
    assert user.is_in_working_hours(_16_59_utc, tz=tz) is False
    assert user.is_in_working_hours(_17_utc, tz=tz) is True
    assert user.is_in_working_hours(_18_utc, tz=tz) is True
    assert user.is_in_working_hours(_18_01_utc, tz=tz) is False


@pytest.mark.django_db
def test_is_in_working_hours_no_timezone(make_organization, make_user_for_organization):
    organization = make_organization()
    user = make_user_for_organization(organization, _timezone=None)

    assert user.is_in_working_hours(timezone.now()) is False


@pytest.mark.django_db
def test_is_in_working_hours_weekend(make_organization, make_user_for_organization):
    organization = make_organization()
    user = make_user_for_organization(organization, working_hours={"saturday": []}, _timezone=None)

    on_saturday = timezone.datetime(2023, 8, 5, 12, 0, 0, tzinfo=datetime.timezone.utc)
    assert user.is_in_working_hours(on_saturday, "UTC") is False


@pytest.mark.django_db
def test_is_telegram_connected(make_organization_and_user, make_telegram_user_connector):
    _, user = make_organization_and_user()
    assert user.is_telegram_connected is False
    make_telegram_user_connector(user)
    assert user.is_telegram_connected is True


@pytest.mark.django_db
def test_has_google_oauth2_connected(make_organization_and_user, make_google_oauth2_user_for_user):
    _, user = make_organization_and_user()

    assert user.has_google_oauth2_connected is False
    make_google_oauth2_user_for_user(user)
    assert user.has_google_oauth2_connected is True


@pytest.mark.django_db
def test_google_oauth2_token_is_missing_scopes(make_organization_and_user):
    initial_granted_scope = "foo bar baz"
    initial_oauth_response = {
        "access_token": "access",
        "refresh_token": "refresh",
        "sub": "google_user_id",
        "scope": initial_granted_scope,
    }

    _, user = make_organization_and_user()

    # false because the user hasn't yet connected their google account
    assert user.google_oauth2_token_is_missing_scopes is False

    user.save_google_oauth2_settings(initial_oauth_response)
    user.refresh_from_db()

    # true because we're missing a granted scope
    assert user.google_oauth2_token_is_missing_scopes is True

    user.save_google_oauth2_settings(
        {
            **initial_oauth_response,
            "scope": f"{initial_granted_scope} {' '.join(google_constants.REQUIRED_OAUTH_SCOPES)}",
        }
    )
    user.refresh_from_db()

    # False because we now have all the required scopes
    assert user.google_oauth2_token_is_missing_scopes is False


@pytest.mark.django_db
def test_save_google_oauth2_settings(make_organization_and_user):
    oauth_response = {
        "access_token": "access",
        "refresh_token": "refresh",
        "sub": "google_user_id",
        "scope": "scope",
    }

    _, user = make_organization_and_user()

    assert GoogleOAuth2User.objects.filter(user=user).exists() is False
    assert user.google_calendar_settings is None

    user.save_google_oauth2_settings(oauth_response)
    user.refresh_from_db()

    google_oauth_user = user.google_oauth2_user
    assert google_oauth_user.google_user_id == "google_user_id"
    assert google_oauth_user.access_token == "access"
    assert google_oauth_user.refresh_token == "refresh"
    assert google_oauth_user.oauth_scope == "scope"
    assert user.google_calendar_settings["oncall_schedules_to_consider_for_shift_swaps"] == []

    oauth_response2 = {
        "access_token": "access2",
        "refresh_token": "refresh2",
        "sub": "google_user_id2",
        "scope": "scope2",
    }

    user.save_google_oauth2_settings(oauth_response2)
    user.refresh_from_db()

    google_oauth_user = user.google_oauth2_user
    assert google_oauth_user.google_user_id == "google_user_id2"
    assert google_oauth_user.access_token == "access2"
    assert google_oauth_user.refresh_token == "refresh2"
    assert google_oauth_user.oauth_scope == "scope2"


@pytest.mark.django_db
def test_reset_google_oauth2_settings(make_organization_and_user):
    _, user = make_organization_and_user()

    user.save_google_oauth2_settings(
        {
            "access_token": "access",
            "refresh_token": "refresh",
            "sub": "google_user_id",
            "scope": "scope",
        }
    )
    user.refresh_from_db()

    assert user.google_oauth2_user is not None
    assert user.google_calendar_settings is not None

    user.reset_google_oauth2_settings()
    user.refresh_from_db()

    assert GoogleOAuth2User.objects.filter(user=user).exists() is False
    assert user.google_calendar_settings is None


@pytest.mark.django_db
def test_filter_by_permission(make_organization, make_user_for_organization):
    """
    Note that there are some conditions in `UserQuerySet.filter_by_permission` that're
    specific to which database engine is being used. These cases are tested on CI where
    we run the test against sqlite, mysql, and postgresql
    """
    permission_to_test = permissions.RBACPermission.Permissions.ALERT_GROUPS_READ
    user_permissions = permissions.GrafanaAPIPermissions.construct_permissions([permission_to_test.value])
    irm_permissions = permissions.GrafanaAPIPermissions.construct_permissions(
        [permissions.convert_oncall_permission_to_irm(permission_to_test)]
    )

    org1_rbac = make_organization(is_rbac_permissions_enabled=True)
    user1 = make_user_for_organization(org1_rbac, permissions=user_permissions)
    user2 = make_user_for_organization(org1_rbac, permissions=user_permissions)
    _ = make_user_for_organization(org1_rbac, permissions=[])

    org2_rbac_irm = make_organization(is_rbac_permissions_enabled=True, is_grafana_irm_enabled=True)
    user4 = make_user_for_organization(org2_rbac_irm, permissions=irm_permissions)
    user5 = make_user_for_organization(org2_rbac_irm, permissions=irm_permissions)
    _ = make_user_for_organization(org2_rbac_irm, permissions=[])

    org3_no_rbac = make_organization(is_rbac_permissions_enabled=False)
    user7 = make_user_for_organization(org3_no_rbac, role=permission_to_test.fallback_role)
    user8 = make_user_for_organization(org3_no_rbac, role=permission_to_test.fallback_role)
    _ = make_user_for_organization(org3_no_rbac, role=permissions.LegacyAccessControlRole.NONE)

    # rbac permissions enabled
    users = User.objects.filter_by_permission(permission_to_test, org1_rbac)

    assert len(users) == 2
    assert user1 in users
    assert user2 in users

    # rbac permissions + IRM enabled
    users = User.objects.filter_by_permission(permission_to_test, org2_rbac_irm)

    assert len(users) == 2
    assert user4 in users
    assert user5 in users

    # rbac permissions disabled
    users = User.objects.filter_by_permission(permission_to_test, org3_no_rbac)

    assert len(users) == 2
    assert user7 in users
    assert user8 in users
