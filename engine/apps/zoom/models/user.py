from django.db import models


class ZoomUser(models.Model):
    """Model to link OnCall users with their Zoom accounts."""

    user = models.OneToOneField(
        "user_management.User",
        on_delete=models.CASCADE,
        related_name="zoom_user_identity",
    )
    zoom_user_id = models.CharField(max_length=100)
    email = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["zoom_user_id"]),
        ]

    def __str__(self):
        return f"ZoomUser({self.email})"

    @property
    def mention_format(self):
        """Return the format to mention this user in Zoom Team Chat."""
        # Zoom uses email-based mentions in the format <at email="user@example.com">Display Name</at>
        return f'<at email="{self.email}">{self.display_name or self.email}</at>'
