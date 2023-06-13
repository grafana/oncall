from django.apps import apps
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

    def notifications_limit_web_report(self, user):
        limits_to_show = []
        left = self._calculate_phone_notifications_left(user)
        limit = self._phone_notifications_limit
        limits_to_show.append({"limit_title": "Phone Calls & SMS", "total": limit, "left": left})
        show_limits_warning = left <= limit * 0.2  # Show limit popup if less than 20% of notifications left

        warning_text = (
            f"You{'' if left == 0 else ' almost'} have exceeded the limit of phone calls and sms:"
            f" {left} of {limit} left."
        )

        return {
            "period_title": "Daily limit",
            "limits_to_show": limits_to_show,
            "show_limits_warning": show_limits_warning,
            "warning_text": warning_text,
        }

    def _calculate_phone_notifications_left(self, user):
        """
        Count sms and calls together and they have common limit.
        For FreePublicBetaSubscriptionStrategy notifications are counted per day
        """
        PhoneCallRecord = apps.get_model("phone_notifications", "PhoneCallRecord")
        SMSMessage = apps.get_model("phone_notifications", "SMSRecord")
        now = timezone.now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        calls_today = PhoneCallRecord.objects.filter(
            created_at__gte=day_start,
            receiver=user,
        ).count()
        sms_today = SMSMessage.objects.filter(
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
