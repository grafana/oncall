from django.db import models

from apps.phone_notifications.phone_provider import ProviderPhoneCall


class ExotelCallStatuses:
    QUEUED = 10
    IN_PROGRESS = 20
    COMPLETED = 30
    FAILED = 40
    BUSY = 50
    NO_ANSWER = 60

    CHOICES = (
        (QUEUED, "queued"),
        (IN_PROGRESS, "in-progress"),
        (COMPLETED, "completed"),
        (FAILED, "failed"),
        (BUSY, "busy"),
        (NO_ANSWER, "no-answer"),
    )

    DETERMINANT = {
        "queued": QUEUED,
        "in-progress": IN_PROGRESS,
        "completed": COMPLETED,
        "failed": FAILED,
        "busy": BUSY,
        "no-answer": NO_ANSWER,
    }


class ExotelPhoneCall(ProviderPhoneCall, models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        choices=ExotelCallStatuses.CHOICES,
    )

    call_id = models.CharField(
        blank=True,
        max_length=50,
    )
