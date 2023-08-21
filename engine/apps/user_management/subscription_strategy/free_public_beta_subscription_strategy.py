from django.conf import settings
from django.utils import timezone

from apps.email.models import EmailMessage

from .base_subsription_strategy import BaseSubscriptionStrategy


class FreePublicBetaSubscriptionStrategy(BaseSubscriptionStrategy):
    """
    This is subscription for beta inside grafana.
    This subscription is responsible only for limiting calls, sms and emails. Notifications limited per user per day.
    User management and limitations happens on grafana side.
    """

    def phone_calls_left(self, user):
        return self._calculate_phone_notifications_left(user)

    def sms_left(self, user):
        return self._calculate_phone_notifications_left(user)

    # todo: manage backend specific limits in messaging backend
    def emails_left(self, user):
        now = timezone.now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        emails_today = EmailMessage.objects.filter(
            created_at__gte=day_start,
            represents_alert_group__channel__organization=self.organization,
            receiver=user,
        ).count()
        return self._emails_limit - emails_today

    def _calculate_phone_notifications_left(self, user):
        """
        Count sms and calls together and they have common limit.
        For FreePublicBetaSubscriptionStrategy notifications are counted per day
        """
        from apps.phone_notifications.models import PhoneCallRecord, SMSRecord

        now = timezone.now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        calls_today = PhoneCallRecord.objects.filter(
            created_at__gte=day_start,
            receiver=user,
        ).count()
        sms_today = SMSRecord.objects.filter(
            created_at__gte=day_start,
            receiver=user,
        ).count()

        return self._phone_notifications_limit - calls_today - sms_today

    @property
    def _phone_notifications_limit(self):
        return settings.PHONE_NOTIFICATIONS_LIMIT

    @property
    def _emails_limit(self):
        return settings.EMAIL_NOTIFICATIONS_LIMIT
