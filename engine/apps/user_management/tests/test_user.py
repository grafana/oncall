import datetime

import pytest
from django.utils import timezone

from apps.api.permissions import LegacyAccessControlRole
from apps.google.models import GoogleOAuth2User
from apps.user_management.models import User


@pytest.mark.django_db
def test_self_or_admin(make_organization, make_user_for_organization):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    second_admin = make_user_for_organization(organization)
    editor = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)

    another_organization = make_organization()
    admin_from_another_organization = make_user_for_organization(another_organization)

    assert admin.self_or_admin(admin, organization) is True
    assert admin.self_or_admin(editor, organization) is False
    assert admin.self_or_admin(second_admin, organization) is True
    assert admin.self_or_admin(admin_from_another_organization, organization) is False


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
def test_finish_google_oauth2_connection_flow(make_organization_and_user):
    oauth_response = {
        "access_token": "access",
        "refresh_token": "refresh",
        "sub": "google_user_id",
        "scope": "scope",
    }

    _, user = make_organization_and_user()

    assert GoogleOAuth2User.objects.filter(user=user).exists() is False
    assert user.google_calendar_settings is None

    user.finish_google_oauth2_connection_flow(oauth_response)
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

    user.finish_google_oauth2_connection_flow(oauth_response2)
    user.refresh_from_db()

    google_oauth_user = user.google_oauth2_user
    assert google_oauth_user.google_user_id == "google_user_id2"
    assert google_oauth_user.access_token == "access2"
    assert google_oauth_user.refresh_token == "refresh2"
    assert google_oauth_user.oauth_scope == "scope2"


@pytest.mark.django_db
def test_finish_google_oauth2_disconnection_flow(make_organization_and_user):
    _, user = make_organization_and_user()

    user.finish_google_oauth2_connection_flow(
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

    user.finish_google_oauth2_disconnection_flow()
    user.refresh_from_db()

    assert GoogleOAuth2User.objects.filter(user=user).exists() is False
    assert user.google_calendar_settings is None
