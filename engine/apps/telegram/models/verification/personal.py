from typing import Optional, Tuple
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.telegram.models import TelegramToUserConnector
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log


class TelegramVerificationCode(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    datetime = models.DateTimeField(auto_now_add=True)

    user = models.OneToOneField(
        "user_management.User", on_delete=models.CASCADE, related_name="telegram_verification_code"
    )

    @property
    def is_active(self) -> bool:
        return self.datetime + timezone.timedelta(days=1) < timezone.now()

    @classmethod
    def verify_user(
        cls, uuid_code: str, telegram_chat_id: int, telegram_nick_name: str
    ) -> Tuple[Optional[TelegramToUserConnector], bool]:
        try:
            verification_code = cls.objects.get(uuid=uuid_code)
            user = verification_code.user

            connector, created = TelegramToUserConnector.objects.get_or_create(
                user=user, telegram_chat_id=telegram_chat_id, defaults={"telegram_nick_name": telegram_nick_name}
            )

            description = f"Telegram account of user {user.username} was connected"
            create_organization_log(
                user.organization,
                user,
                OrganizationLogType.TYPE_TELEGRAM_TO_USER_CONNECTED,
                description,
            )
            return connector, created

        except (ValidationError, cls.DoesNotExist):
            return None, False
