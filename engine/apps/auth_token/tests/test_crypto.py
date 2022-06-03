import binascii
from hmac import compare_digest

from apps.auth_token.crypto import (
    generate_plugin_token_string,
    generate_plugin_token_string_and_salt,
    hash_token_string,
)


def test_plugin_token_round_trip():
    stack_id = 100
    org_id = 100

    hex_token, hex_salt = generate_plugin_token_string_and_salt(stack_id, org_id)
    hex_signature = hash_token_string(hex_token)

    raw_salt = binascii.unhexlify(hex_salt)
    hex_recreated_token = generate_plugin_token_string(raw_salt, stack_id, org_id)
    hex_recreated_signature = hash_token_string(hex_recreated_token)

    assert hex_token == hex_recreated_token
    assert compare_digest(hex_signature, hex_recreated_signature)
