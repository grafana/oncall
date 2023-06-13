import datetime
from typing import Optional, Tuple
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models
from django.utils import timezone

from apps.telegram.models import TelegramToUserConnector
from common.insight_log import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log


class TelegramVerificationCode(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    datetime = models.DateTimeField(auto_now_add=True)

    user = models.OneToOneField(
        "user_management.User", on_delete=models.CASCADE, related_name="telegram_verification_code"
    )

    @property
    def is_active(self) -> bool:
        return self.datetime + datetime.timedelta(days=1) < timezone.now()

    @property
    def uuid_with_org_uuid(self) -> str:
        return f"{self.user.organization.uuid}_{self.uuid}"

    @classmethod
    def uuid_without_org_id(cls, verification_code: str) -> str:
        try:
            return verification_code.split("_")[1]
        except IndexError:
            raise ValidationError("Invalid verification code format")

    @classmethod
    def verify_user(
        cls, verification_code: str, telegram_chat_id: int, telegram_nick_name: str
    ) -> Tuple[Optional[TelegramToUserConnector], bool]:
        try:
            uuid_code = cls.uuid_without_org_id(verification_code)
            code_instance = cls.objects.get(uuid=uuid_code)

            user = code_instance.user

            connector, created = TelegramToUserConnector.objects.get_or_create(
                user=user, defaults={"telegram_nick_name": telegram_nick_name, "telegram_chat_id": telegram_chat_id}
            )
            write_chatops_insight_log(
                author=user,
                event_name=ChatOpsEvent.USER_LINKED,
                chatops_type=ChatOpsTypePlug.TELEGRAM.value,
                linked_user=user.username,
                linked_user_id=user.public_primary_key,
            )
            return connector, created

        except (ValidationError, cls.DoesNotExist, IntegrityError):
            return None, False
