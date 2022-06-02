from rest_framework.permissions import BasePermission

from apps.base.utils import live_settings


class AllowOnlySendgrid(BasePermission):
    def has_permission(self, request, view):
        # https://stackoverflow.com/questions/20865673/sendgrid-incoming-mail-webhook-how-do-i-secure-my-endpoint
        sendgrid_key = request.query_params.get("key")

        if sendgrid_key is None:
            return False

        return live_settings.SENDGRID_SECRET_KEY == sendgrid_key
