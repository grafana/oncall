import logging
from urllib.parse import urlparse

from ipware import get_client_ip

from common.recaptcha import check_recaptcha_v3

logger = logging.getLogger(__name__)


def check_recaptcha_internal_api(request, action: str, score=0.5) -> bool:
    """
    Helper function to perform recaptcha checks in internal api.
    Assumes, that request is authenticated and recaptcha value passed in X-OnCall-Recaptcha header.
    """
    client_ip, _ = get_client_ip(request)
    recaptcha_value = request.headers.get("X-OnCall-Recaptcha", "some-non-null-value")
    org_hostname = urlparse(request.auth.organization.grafana_url).hostname
    return check_recaptcha_v3(recaptcha_value, action, score, client_ip, org_hostname)
