import base64
import binascii
import hashlib
import hmac


def hash(data):
    hasher = hashlib.sha256()
    hasher.update(data)
    return base64.b64encode(hasher.digest()).decode()


def generate_signature(data, secret):
    h = hmac.new(secret.encode(), data.encode(), hashlib.sha256)
    return binascii.hexlify(h.digest()).decode()


def verify_signature(request, secret) -> bool:
    header = request.META.get("HTTP_X_CHATOPS_SIGNATURE")
    if not header:
        return False

    signatures = header.split(",")
    s = dict(pair.split("=") for pair in signatures)
    t = s.get("t")
    v1 = s.get("v1")

    payload = request.body
    body_hash = hash(payload)
    string_to_sign = f"{body_hash}:{t}:v1"
    expected = generate_signature(string_to_sign, secret)

    if expected != v1:
        return False

    return True
