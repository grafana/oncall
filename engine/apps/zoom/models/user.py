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
    def user_jid(self):
        """Return the user JID for Zoom Team Chat API."""
        return f"{self.zoom_user_id}@xmpp.zoom.us"

    @property
    def mention_format(self):
        """
        Return the format to mention this user in Zoom Team Chat.
        
        Uses the JID-based mention format: <!user_jid|Display Name>
        This format works in both regular messages and interactive card messages.
        """
        display = self.display_name or self.email
        return f"<!{self.user_jid}|{display}>"
