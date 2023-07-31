import datetime
from typing import Optional, Tuple
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.telegram.models import TelegramToOrganizationConnector
from common.insight_log.chatops_insight_logs import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log


class TelegramChannelVerificationCode(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    datetime = models.DateTimeField(auto_now_add=True)

    organization = models.OneToOneField(
        "user_management.Organization", on_delete=models.CASCADE, related_name="telegram_verification_code"
    )

    author = models.ForeignKey("user_management.User", on_delete=models.CASCADE, null=True, default=None)

    @property
    def is_active(self) -> bool:
        return self.datetime + datetime.timedelta(days=1) < timezone.now()

    @property
    def uuid_with_org_uuid(self) -> str:
        return f"{self.organization.uuid}_{self.uuid}"

    @classmethod
    def uuid_without_org_id(cls, verification_code: str) -> str:
        try:
            return verification_code.split("_")[1]
        except IndexError:
            raise ValidationError("Invalid verification code format")

    @classmethod
    def verify_channel_and_discussion_group(
        cls,
        verification_code: str,
        channel_chat_id: int,
        channel_name: str,
        discussion_group_chat_id: int,
        discussion_group_name: str,
    ) -> Tuple[Optional[TelegramToOrganizationConnector], bool]:
        try:
            uuid_code = cls.uuid_without_org_id(verification_code)

            code_instance = cls.objects.get(uuid=uuid_code)

            # see if a organization has other channels connected
            # if it is the first channel, make it default for the organization
            connector_exists = code_instance.organization.telegram_channel.exists()

            connector, created = TelegramToOrganizationConnector.objects.get_or_create(
                channel_chat_id=channel_chat_id,
                defaults={
                    "organization": code_instance.organization,
                    "channel_name": channel_name,
                    "discussion_group_chat_id": discussion_group_chat_id,
                    "discussion_group_name": discussion_group_name,
                    "is_default_channel": not connector_exists,
                },
            )

            write_chatops_insight_log(
                author=code_instance.author,
                event_name=ChatOpsEvent.CHANNEL_CONNECTED,
                chatops_type=ChatOpsTypePlug.TELEGRAM.value,
                channel_name=channel_name,
            )
            if not connector_exists:
                write_chatops_insight_log(
                    author=code_instance.author,
                    event_name=ChatOpsEvent.DEFAULT_CHANNEL_CHANGED,
                    chatops_type=ChatOpsTypePlug.TELEGRAM.value,
                    prev_channel=None,
                    new_channel=channel_name,
                )

            return connector, created

        except (ValidationError, cls.DoesNotExist):
            return None, False
