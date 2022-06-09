import logging
from contextlib import suppress

from django.apps import apps
from django.utils import timezone

from apps.public_api.constants import DEMO_USER_ID
from apps.schedules.ical_utils import list_users_to_notify_from_ical_for_period

logger = logging.getLogger(__name__)


def active_oss_users_count():
    """
    active_oss_users_count returns count of active users of oss installation.
    """
    OnCallSchedule = apps.get_model("schedules", "OnCallSchedule")
    AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")
    EscalationPolicy = apps.get_model("alerts", "EscalationPolicy")
    UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")
    User = apps.get_model("user_management", "User")

    # Take logs for previous 24 hours
    start = timezone.now() - timezone.timedelta(hours=24)
    end = timezone.now()

    # Take schedules for current month
    schedule_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    schedule_end = (schedule_start + timezone.timedelta(days=32)).replace(day=1)

    unique_active_users = set()

    unique_active_users.update(
        list(
            UserNotificationPolicyLogRecord.objects.filter(
                created_at__gte=start, created_at__lt=end, author__isnull=False
            )
            .values_list("author_id", flat=True)
            .distinct()
        )
    )

    unique_active_users.update(
        list(
            AlertGroupLogRecord.objects.filter(
                type__in=AlertGroupLogRecord.TYPES_FOR_LICENCE_CALCULATION,
                created_at__gte=start,
                created_at__lt=end,
                author__isnull=False,
            )
            .values_list("author_id", flat=True)
            .distinct()
        )
    )

    # Get active users from notification policies
    unique_active_users.update(
        list(
            EscalationPolicy.objects.filter(notify_to_users_queue__isnull=False).values_list(
                "notify_to_users_queue__id", flat=True
            )
        )
    )

    for schedule in OnCallSchedule.objects.all():
        users_from_schedule = list_users_to_notify_from_ical_for_period(schedule, schedule_start, schedule_end)
        for user in users_from_schedule:
            unique_active_users.add(user.pk)

    # Remove demo user from active users
    with suppress(User.DoesNotExist):
        demo_user = User.objects.get(public_primary_key=DEMO_USER_ID)
        with suppress(KeyError):
            unique_active_users.remove(demo_user.pk)
    return len(unique_active_users)
