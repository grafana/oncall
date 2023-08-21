from unittest.mock import patch

import pytest

from apps.schedules.models import OnCallScheduleWeb
from apps.schedules.tasks.drop_cached_ical import drop_cached_ical_task


@pytest.mark.django_db
def test_drop_cached_ical_triggers_final_refresh(make_organization, make_schedule):
    organization = make_organization()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    with patch("apps.schedules.tasks.drop_cached_ical.refresh_ical_final_schedule") as mock_refresh_final:
        drop_cached_ical_task(schedule.pk)
        assert mock_refresh_final.apply_async.called
