import binascii
from os import urandom as generate_bytes
from typing import Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.hashes import SHA512

from apps.auth_token import constants

sha = SHA512


def generate_token_string() -> str:
    num_bytes = int(constants.AUTH_TOKEN_CHARACTER_LENGTH / 2)
    return binascii.hexlify(generate_bytes(num_bytes)).decode()


def generate_short_token_string() -> str:
    num_bytes = int(constants.AUTH_SHORT_TOKEN_CHARACTER_LENGTH / 2)
    return binascii.hexlify(generate_bytes(num_bytes)).decode()


def hash_token_string(token_string: str) -> str:
    digest = hashes.Hash(sha(), backend=default_backend())
    digest.update(binascii.unhexlify(token_string))
    return binascii.hexlify(digest.finalize()).decode()


def generate_plugin_token_string_and_salt(stack_id: int, org_id: int) -> Tuple[str, str]:
    random_salt = generate_bytes(int(constants.AUTH_TOKEN_CHARACTER_LENGTH / 2))
    return generate_plugin_token_string(random_salt, stack_id, org_id), binascii.hexlify(random_salt).decode()


def generate_plugin_token_string(salt: bytes, stack_id: int, org_id: int) -> str:
    digest = hashes.Hash(sha(), backend=default_backend())
    digest.update(salt)
    digest.update(bytes(stack_id))
    digest.update(bytes(org_id))
    return binascii.hexlify(digest.finalize()).decode()


def generate_schedule_token_string() -> str:
    num_bytes = int(constants.SCHEDULE_EXPORT_TOKEN_CHARACTER_LENGTH / 2)
    return binascii.hexlify(generate_bytes(num_bytes)).decode()
