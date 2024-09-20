from django.db import models


class MattermostUser(models.Model):
    user = models.OneToOneField("user_management.User", on_delete=models.CASCADE, related_name="mattermost_connection")
    mattermost_user_id = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    nickname = models.CharField(max_length=100, null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "mattermost_user_id")
