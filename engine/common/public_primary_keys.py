import logging

from django.conf import settings
from django.core.exceptions import FieldError
from django.utils.crypto import get_random_string

logger = logging.getLogger(__name__)


def generate_public_primary_key(prefix, length=settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH):
    """It generates random string with prefix and length
    :param prefix:
            "U": ("user_management", "User"),
            "O": ("user_management", "Organization"),
            "T": ("user_management", "Team"),
            "N": ("base", "UserNotificationPolicy"),
            "C": ("alerts", "AlertReceiveChannel"),
            "R": ("alerts", "ChannelFilter"),
            "S": ("schedules", "OnCallSchedule"),
            "E": ("alerts", "EscalationPolicy"),
            "F": ("alerts", "EscalationChain"),
            "I": ("alerts", "AlertGroup"),
            "A": ("alerts", "Alert"),
            "M": ("alerts", "ResolutionNote"),
            "G": ("slack", "SlackUserGroup"),
            "K": ("alerts", "CustomButton"),
            "O": ("schedules", "CustomOnCallShift"),
            "B": ("heartbeat", "IntegrationHeartBeat"),
            "H": ("slack", "SlackChannel"),
            "Z": ("telegram", "TelegramToOrganizationConnector"),
            "L": ("base", "LiveSetting"),
            "X": ("extensions", "Other models from extensions apps"),
    :param length:
    :return:
    """

    return prefix + get_random_string(length=length, allowed_chars=settings.PUBLIC_PRIMARY_KEY_ALLOWED_CHARS)


def increase_public_primary_key_length(failure_counter, prefix, model_name, max_attempt_count=5):
    """
    Another yet helper which generates random string with larger length
    when previous public_primary_key exists

    :param failure_counter:
    :param prefix:
    :param model_name:
    :param max_attempt_count: When attempt count is more then max_attempt_count we'll get the exception
    :return:
    """

    if failure_counter < max_attempt_count:
        logger.warning(
            f"Let's try increase a {model_name} "
            f"new_public_primary_key length "
            f"({failure_counter + 1}/{max_attempt_count}) times"
        )

        return generate_public_primary_key(
            prefix=prefix, length=settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + failure_counter
        )
    else:
        raise FieldError(
            f"A count of {model_name} new_public_primary_key generation " f"attempts is more than {max_attempt_count}!"
        )
