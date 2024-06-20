import json
import logging
from dataclasses import asdict, dataclass
from typing import List

from django.db import models

from apps.phone_notifications.exceptions import PhoneNumberBanned

logger = logging.getLogger(__name__)


@dataclass
class BannedPhoneUserEntry:
    user_id: int
    user_name: str
    org_id: int
    stack_slug: str
    org_slug: str


class BannedPhoneNumber(models.Model):
    phone_number = models.CharField(primary_key=True, max_length=20)
    created_at = models.DateTimeField(auto_now=True)
    reason = models.TextField(null=True, default=None)
    users = models.JSONField(null=True, default=None)

    def get_user_entries(self) -> List[BannedPhoneUserEntry]:
        return [BannedPhoneUserEntry(**data) for data in json.loads(self.users)]


def ban_phone_number(phone_number: str, reason: str):
    from apps.user_management.models import User

    banned_phone_number = BannedPhoneNumber(phone_number=phone_number)
    users = User.objects.filter(_verified_phone_number=phone_number)
    # Record instances of phone number use
    user_entries = [
        asdict(
            BannedPhoneUserEntry(
                user_id=user.id,
                user_name=user.username,
                org_id=user.organization.org_id,
                stack_slug=user.organization.stack_slug,
                org_slug=user.organization.org_slug,
            )
        )
        for user in users
    ]
    users.update(_verified_phone_number=None)
    banned_phone_number.users = json.dumps(user_entries)
    banned_phone_number.reason = reason
    banned_phone_number.save()

    logger.info(f"ban_phone_number={phone_number}, in use by users={len(user_entries)}, reason={reason}")


def check_banned_phone_number(phone_number: str):
    banned_entry = BannedPhoneNumber.objects.filter(phone_number=phone_number).first()
    if banned_entry:
        raise PhoneNumberBanned
