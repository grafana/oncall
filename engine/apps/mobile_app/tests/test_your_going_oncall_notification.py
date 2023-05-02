from unittest import mock

import pytest
from django.utils import timezone
from fcm_django.models import FCMDevice

from apps.mobile_app.models import MobileAppUserSettings
from apps.mobile_app.tasks import (
    conditionally_send_going_oncall_push_notifications_for_all_schedules,
    conditionally_send_going_oncall_push_notifications_for_schedule,
    should_we_send_going_oncall_push_notification,
)
from apps.schedules.models import OnCallScheduleCalendar, OnCallScheduleICal, OnCallScheduleWeb
from apps.schedules.models.on_call_schedule import ScheduleEvent

MOBILE_APP_BACKEND_ID = 5
CLOUD_LICENSE_NAME = "Cloud"
OPEN_SOURCE_LICENSE_NAME = "OpenSource"


def _create_schedule_event() -> ScheduleEvent:
    return {
        # TODO:
        "start": timezone.now(),
    }


@pytest.mark.django_db
def test_should_we_send_going_oncall_push_notification(make_organization_and_user, make_schedule):
    # create a user and connect a mobile device
    organization, user = make_organization_and_user()
    FCMDevice.objects.create(user=user, registration_id="test_device_id")

    now = timezone.now()

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    print(schedule)
    user_mobile_settings = MobileAppUserSettings.objects.create(user=user, important_notification_override_dnd=False)

    # TODO: finish test
    should_we_send_going_oncall_push_notification(now, user_mobile_settings, _create_schedule_event())


@pytest.mark.django_db
def test_conditionally_send_going_oncall_push_notifications_for_schedule(make_organization_and_user, make_schedule):
    # create a user and connect a mobile device
    organization, user = make_organization_and_user()
    FCMDevice.objects.create(user=user, registration_id="test_device_id")

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    # TODO: finish test
    conditionally_send_going_oncall_push_notifications_for_schedule(schedule.pk)


@mock.patch("apps.mobile_app.tasks.conditionally_send_going_oncall_push_notifications_for_schedule", return_value=None)
@pytest.mark.django_db
def test_conditionally_send_going_oncall_push_notifications_for_all_schedules(
    mocked_conditionally_send_going_oncall_push_notifications_for_schedule,
    make_organization_and_user,
    make_schedule,
):
    # create a user and connect a mobile device
    organization, user = make_organization_and_user()
    FCMDevice.objects.create(user=user, registration_id="test_device_id")

    schedule1 = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    schedule2 = make_schedule(organization, schedule_class=OnCallScheduleICal)
    schedule3 = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    conditionally_send_going_oncall_push_notifications_for_all_schedules()

    mocked_conditionally_send_going_oncall_push_notifications_for_schedule.apply_async.assert_has_calls(
        [
            mock.call((schedule1.pk,)),
            mock.call((schedule2.pk,)),
            mock.call((schedule3.pk,)),
        ],
        any_order=True,
    )
