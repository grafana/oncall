from unittest.mock import patch

import pytest

from apps.schedules.models import OnCallScheduleICal
from apps.schedules.tasks.refresh_ical_files import refresh_ical_file


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
                    "apps.schedules.tasks.refresh_ical_files.notify_about_empty_shifts_in_schedule"
                ) as mock_notify_empty:
                    with patch(
                        "apps.schedules.tasks.refresh_ical_files.notify_about_gaps_in_schedule"
                    ) as mock_notify_gaps:
                        refresh_ical_file(schedule.pk)

        assert mock_notify_empty.apply_async.called == run_task
        assert mock_notify_gaps.apply_async.called == run_task
