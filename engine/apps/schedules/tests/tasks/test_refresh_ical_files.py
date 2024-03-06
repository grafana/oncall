import datetime
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.utils import timezone

from apps.schedules.models import CustomOnCallShift, OnCallScheduleICal, OnCallScheduleWeb
from apps.schedules.tasks.refresh_ical_files import refresh_ical_file, start_refresh_ical_files


@pytest.mark.django_db
@pytest.mark.parametrize(
    "cached_ical_primary,prev_ical_primary,cached_ical_overrides,prev_ical_overrides,run_task",
    [
        ("ical data", "", None, None, True),
        (None, None, "ical data", "", True),
        ("", "ical data", None, None, False),
        (None, None, "", "ical data", False),
        ("ical data", "diff data", None, None, True),
        ("ical data", "ical data", None, None, False),
        (None, None, "ical data", "diff data", True),
        (None, None, "ical data", "ical data", False),
    ],
)
def test_refresh_ical_file_trigger_run(
    cached_ical_primary,
    prev_ical_primary,
    cached_ical_overrides,
    prev_ical_overrides,
    run_task,
    make_organization,
    make_schedule,
):
    organization = make_organization()
    # set schedule ical file status *after* refresh
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        cached_ical_file_primary=cached_ical_primary,
        prev_ical_file_primary=prev_ical_primary,
        cached_ical_file_overrides=cached_ical_overrides,
        prev_ical_file_overrides=prev_ical_overrides,
    )

    # patch ical comparison to string compare
    with patch("apps.schedules.tasks.refresh_ical_files.is_icals_equal", side_effect=lambda a, b: a == b):
        # patch schedule refresh to avoid changing schedule status (keep as defined above)
        with patch("apps.schedules.models.OnCallSchedule.refresh_ical_file", return_value=None):
            # do not trigger tasks for real
            with patch("apps.schedules.tasks.refresh_ical_files.notify_ical_schedule_shift"):
                with patch(
                    "apps.schedules.tasks.refresh_ical_files.notify_about_empty_shifts_in_schedule_task"
                ) as mock_notify_empty:
                    with patch(
                        "apps.schedules.tasks.refresh_ical_files.notify_about_gaps_in_schedule_task"
                    ) as mock_notify_gaps:
                        refresh_ical_file(schedule.pk)

        assert mock_notify_empty.apply_async.called == run_task
        assert mock_notify_gaps.apply_async.called == run_task


@pytest.mark.django_db
@patch("apps.slack.tasks.start_update_slack_user_group_for_schedules.apply_async")
def test_refresh_ical_files_filter_orgs(
    mocked_start_update_slack_user_group_for_schedules,
    make_organization,
    make_schedule,
):
    organization = make_organization()
    deleted_organization = make_organization(deleted_at=datetime.datetime.now())

    schedule_from_deleted_org = make_schedule(deleted_organization, schedule_class=OnCallScheduleWeb)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    with patch("apps.schedules.tasks.refresh_ical_file.apply_async") as mocked_refresh_ical_file:
        start_refresh_ical_files()
        assert mocked_refresh_ical_file.called
        called_args = mocked_refresh_ical_file.call_args_list
        assert len(called_args) == 1
        assert schedule.id in called_args[0].args[0]
        assert schedule_from_deleted_org.id not in called_args[0].args[0]


@pytest.mark.django_db
def test_refresh_ical_updates_oncall_cache(
    make_organization,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
):
    organization = make_organization()
    users = [make_user_for_organization(organization) for _ in range(2)]

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    shift_start_time = today - timezone.timedelta(hours=1)
    on_call_shift = make_on_call_shift(
        organization=organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        start=shift_start_time,
        rotation_start=shift_start_time,
        duration=timezone.timedelta(seconds=(24 * 60 * 60)),
        priority_level=1,
        frequency=CustomOnCallShift.FREQUENCY_DAILY,
        schedule=schedule,
    )
    on_call_shift.add_rolling_users([users])

    def _generate_cache_key(schedule):
        return f"schedule_oncall_users_{schedule.public_primary_key}"

    # start with empty cache
    cache.clear()

    # patch ical comparison to string compare
    with patch("apps.schedules.tasks.refresh_ical_files.is_icals_equal", side_effect=lambda a, b: a == b):
        # patch schedule refresh to avoid changing schedule status (keep as defined above)
        with patch("apps.schedules.models.OnCallSchedule.refresh_ical_file", return_value=None):
            # do not trigger tasks for real
            with patch("apps.schedules.tasks.refresh_ical_files.notify_ical_schedule_shift"):
                with patch("apps.schedules.tasks.refresh_ical_files.notify_about_empty_shifts_in_schedule_task"):
                    with patch("apps.schedules.tasks.refresh_ical_files.notify_about_gaps_in_schedule_task"):
                        refresh_ical_file(schedule.pk)

    cached_data = cache.get(_generate_cache_key(schedule))
    assert cached_data == [u.public_primary_key for u in users]
