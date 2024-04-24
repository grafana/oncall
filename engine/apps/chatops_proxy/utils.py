import logging
import typing

from django.conf import settings
from rest_framework.request import Request

from common.oncall_gateway.client import ChatopsProxyAPIClient

logger = logging.getLogger(__name__)


def get_installation_link_from_chatops_proxy(request: Request) -> typing.Optional[str]:
    client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)

    try:
        link, _ = client.get_slack_oauth_link(
            request.user.organization.stack_id, request.user.user_id, request.user.organization.web_link
        )
        return link
    except Exception as e:
        logger.exception("Error while getting installation link from chatops proxy: error=%s", e)
        return None
