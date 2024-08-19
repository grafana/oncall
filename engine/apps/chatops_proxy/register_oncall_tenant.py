# register_oncall_tenant moved to separate file from engine/apps/chatops_proxy/utils.py to avoid circular imports.
from django.conf import settings

from apps.chatops_proxy.client import APP_TYPE_ONCALL, ChatopsProxyAPIClient


def register_oncall_tenant(org):
    """
    register_oncall_tenant registers oncall organization as a tenant in chatops-proxy.
    """
    client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    client.register_tenant(
        str(org.uuid),
        settings.ONCALL_BACKEND_REGION,
        APP_TYPE_ONCALL,
        org.stack_id,
        org.stack_slug,
    )
