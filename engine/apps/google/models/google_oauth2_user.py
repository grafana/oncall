from django.db import models


class GoogleOAuth2User(models.Model):

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey("user_management.User", on_delete=models.CASCADE, related_name="google_oauth2_user")
    google_user_id = models.CharField(max_length=100)
    access_token = models.CharField(max_length=255)
    """
    TODO: should `access_token` be encrypted?
    """
    refresh_token = models.CharField(max_length=255)
    """
    TODO: should `refresh_token` be encrypted?
    """
    oauth_scope = models.TextField(max_length=30000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user"], name="unique_google_oauth2_user")]
