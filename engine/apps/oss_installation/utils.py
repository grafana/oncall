import logging
from urllib.parse import urljoin

from django.utils import timezone

from apps.oss_installation import constants as oss_constants
from apps.schedules.ical_utils import list_users_to_notify_from_ical_for_period

logger = logging.getLogger(__name__)


def active_oss_users_count():
    """
    active_oss_users_count returns count of active users of oss installation.
    """
    from apps.alerts.models import AlertGroupLogRecord, EscalationPolicy
    from apps.base.models import UserNotificationPolicyLogRecord
    from apps.schedules.models import OnCallSchedule

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

    return len(unique_active_users)


def cloud_user_identity_status(connector, identity):
    link = None
    if connector is None:
        status = oss_constants.CLOUD_NOT_SYNCED
    elif identity is None:
        status = oss_constants.CLOUD_SYNCED_USER_NOT_FOUND
        link = connector.cloud_url
    else:
        if identity.phone_number_verified:
            status = oss_constants.CLOUD_SYNCED_PHONE_VERIFIED
        else:
            status = oss_constants.CLOUD_SYNCED_PHONE_NOT_VERIFIED

        link = urljoin(connector.cloud_url, f"a/grafana-oncall-app/?page=users&p=1&id={identity.cloud_id}")
    return status, link
