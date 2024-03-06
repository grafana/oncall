import logging

from django.conf import settings
from django.core.exceptions import FieldError
from django.utils.crypto import get_random_string

logger = logging.getLogger(__name__)


def generate_public_primary_key(prefix: str, length: int = settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH) -> str:
    return prefix + get_random_string(length=length, allowed_chars=settings.PUBLIC_PRIMARY_KEY_ALLOWED_CHARS)


def increase_public_primary_key_length(
    failure_counter: int, prefix: str, model_name: str, max_attempt_count: int = 5
) -> str:
    if failure_counter < max_attempt_count:
        logger.warning(
            f"Let's try increase a {model_name} "
            f"new_public_primary_key length "
            f"({failure_counter + 1}/{max_attempt_count}) times"
        )

        return generate_public_primary_key(
            prefix=prefix, length=settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + failure_counter
        )
    raise FieldError(
        f"A count of {model_name} new_public_primary_key generation " f"attempts is more than {max_attempt_count}!"
    )
