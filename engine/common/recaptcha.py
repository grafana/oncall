import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


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
                f"check_recaptcha_v3: "
                f"failed: received action {recaptcha_response['action']} doesn't match defined {action}"
            )
            return False
        if recaptcha_response["score"] <= float(score):
            logger.info(
                f"check_recaptcha_v3:"
                f' failed: received score {recaptcha_response["score"]} lower then required {score}'
            )
            return False
        if settings.RECAPTCHA_V3_HOSTNAME_VALIDATION:
            # https://developers.google.com/recaptcha/docs/domain_validation?hl=en
            if recaptcha_response["hostname"] != hostname:
                logger.info(
                    f"check_recaptcha_v3:"
                    f' failed: received response from hostname {recaptcha_response["score"]},'
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
