from django.db import models


class CloudUserIdentity(models.Model):
    phone_number_verified = models.BooleanField(default=False)
    cloud_id = models.CharField(max_length=20)
    email = models.EmailField()
