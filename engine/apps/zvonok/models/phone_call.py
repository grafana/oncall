from django.db import models

from apps.phone_notifications.phone_provider import ProviderPhoneCall


class ZvonokCallStatuses:
    ATTEMPTS_EXC = 10
    COMPL_FINISHED = 20
    COMPL_NOFINISHED = 30
    DELETED = 40
    DURATION_ERROR = 50
    EXPIRES = 60
    NOVALID_BUTTON = 70
    NO_PROVIDER = 80
    INTERRUPTED = 90
    IN_PROCESS = 100
    PINCODE_NOOK = 110
    PINCODE_OK = 120
    SYNTH_ERROR = 130
    USER = 140

    CHOICES = (
        (ATTEMPTS_EXC, "attempts_exc"),
        (COMPL_FINISHED, "compl_finished"),
        (COMPL_NOFINISHED, "compl_nofinished"),
        (DELETED, "deleted"),
        (DURATION_ERROR, "duration_error"),
        (EXPIRES, "expires"),
        (NOVALID_BUTTON, "novalid_button"),
        (NO_PROVIDER, "no_provider"),
        (INTERRUPTED, "interrupted"),
        (IN_PROCESS, "in_process"),
        (PINCODE_NOOK, "pincode_nook"),
        (SYNTH_ERROR, "synth_error"),
        (USER, "user"),
    )

    DETERMINANT = {
        "attempts_exc": ATTEMPTS_EXC,
        "compl_finished": COMPL_FINISHED,
        "deleted": DELETED,
        "duration_error": DURATION_ERROR,
        "expires": EXPIRES,
        "novalid_button": NOVALID_BUTTON,
        "no_provider": NO_PROVIDER,
        "interrupted": INTERRUPTED,
        "in_process": IN_PROCESS,
        "pincode_nook": PINCODE_NOOK,
        "synth_error": SYNTH_ERROR,
        "user": USER,
    }


class ZvonokPhoneCall(ProviderPhoneCall, models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        choices=ZvonokCallStatuses.CHOICES,
    )

    call_id = models.CharField(
        blank=True,
        max_length=50,
    )

    campaign_id = models.CharField(
        max_length=50,
    )
