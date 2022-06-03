from django.db import models


class CloudUserIdentity(models.Model):
    phone_number_verified = models.BooleanField(default=False)
    cloud_id = models.CharField(max_length=20)
    email = models.EmailField()
    organization = models.ForeignKey(
        "user_management.Organization", on_delete=models.CASCADE, related_name="cloud_users"
    )

    class Meta:
        # TODO: Grafana Twilio: Check if this constraint needed
        unique_together = ("cloud_id", "organization")
