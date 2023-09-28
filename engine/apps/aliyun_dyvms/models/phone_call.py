from django.db import models

from apps.phone_notifications.phone_provider import ProviderPhoneCall


class AliyunDyvmsCallStatuses:
    # see code description: https://help.aliyun.com/document_detail/55085.html?spm=a2c4g.11186623.0.0.44015afcvXbvA5
    USER_COMPLETED = "200000"
    USER_ABORTED = "200001"
    USER_BUSY = "200002"
    USER_NO_ANSWER = "200003"
    USER_DENIED = "200005"
    USER_NOT_IN_ZONE = "200007"
    USER_POWER_OFF = "200010"
    USER_PHONE_OFF = "200011"
    USER_CALL_LIMITED = "200119"
    IN_PROCESS = "200101"

class AliyunDyvmsPhoneCall(ProviderPhoneCall, models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        blank=True,
        null=True,
        max_length=50,
    )

    call_id = models.CharField(
        blank=True,
        max_length=50,
    )