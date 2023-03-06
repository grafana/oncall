import logging
from urllib.parse import urlparse

import requests
from django.conf import settings
from ipware import get_client_ip

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


def check_recaptcha_v3(value: str, action: str, score: float, client_ip: str, hostname=None) -> bool:
    """
    check_recaptcha_v3 performs validation of google recaptcha_v3
    https://developers.google.com/recaptcha/docs/v3?hl=en
    """
    if settings.RECAPTCHA_V3_ENABLED:
        try:
            recaptcha_response = _submit_recaptcha_v3(value, client_ip)
        except requests.HTTPError as exc:
            logger.info(f"check_recaptcha_v3: HTTPError {exc}")
            return False

        # check response structure here https://developers.google.com/recaptcha/docs/v3?hl=en#site_verify_response
        if not recaptcha_response["success"]:
            error_codes = recaptcha_response.get("error-codes", [])
            logger.info(f"check_recaptcha_v3: failed: verification failed {error_codes}")
            return False
        if recaptcha_response["action"] != action:
            logger.info(
                f"check_recaptcha_v3: failed:"
                f" received action {recaptcha_response['action']} doesn't match defined {action}"
            )
            return False
        if recaptcha_response["score"] <= float(score):
            logger.info(
                f"check_recaptcha_v3: failed:"
                f' received score {recaptcha_response["score"]} lower then required {score}'
            )
            return False
        if settings.RECAPTCHA_V3_HOSTNAME_VALIDATION:
            logger.info(
                f"check_recaptcha_v3: start hostname validation "
                f"recaptcha_hostname={recaptcha_response['hostname']} provided_hostname={hostname}"
            )
            # https://developers.google.com/recaptcha/docs/domain_validation?hl=en
            if recaptcha_response["hostname"] != hostname:
                logger.info(
                    f"check_recaptcha_v3:"
                    f' failed: received response from hostname {recaptcha_response["hostname"]},'
                    f" started from {hostname}"
                )
                return False

    return True


def _submit_recaptcha_v3(value: str, client_ip: str) -> dict:
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "User-agent": "Grafana OnCall",
    }
    r = requests.post(
        url="https://www.google.com/recaptcha/api/siteverify",
        data={"secret": settings.RECAPTCHA_V3_SECRET_KEY, "response": value, "remoteip": client_ip},
        headers=headers,
        timeout=10,
    )
    r.raise_for_status()
    return r.json()
