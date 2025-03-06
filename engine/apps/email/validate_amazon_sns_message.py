import logging
import re
from base64 import b64decode
from urllib.parse import urlparse

import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.hashes import SHA1, SHA256
from cryptography.x509 import NameOID, load_pem_x509_certificate
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

HOST_PATTERN = re.compile(r"^sns\.[a-zA-Z0-9\-]{3,}\.amazonaws\.com(\.cn)?$")
REQUIRED_KEYS = (
    "Message",
    "MessageId",
    "Timestamp",
    "TopicArn",
    "Type",
    "Signature",
    "SigningCertURL",
    "SignatureVersion",
)
SIGNING_KEYS_NOTIFICATION = ("Message", "MessageId", "Subject", "Timestamp", "TopicArn", "Type")
SIGNING_KEYS_SUBSCRIPTION = ("Message", "MessageId", "SubscribeURL", "Timestamp", "Token", "TopicArn", "Type")


def validate_amazon_sns_message(message: dict) -> bool:
    """
    Validate an AWS SNS message. Based on:
    - https://docs.aws.amazon.com/sns/latest/dg/sns-verify-signature-of-message.html
    - https://github.com/aws/aws-js-sns-message-validator/blob/a6ba4d646dc60912653357660301f3b25f94d686/index.js
    - https://github.com/aws/aws-php-sns-message-validator/blob/3cee0fc1aee5538e1bd677654b09fad811061d0b/src/MessageValidator.php
    """

    # Check if the message has all the required keys
    if not all(key in message for key in REQUIRED_KEYS):
        logger.warning("Missing required keys in the message, got: %s", message.keys())
        return False

    # Check TopicArn
    if message["TopicArn"] != settings.INBOUND_EMAIL_AMAZON_SNS_TOPIC_ARN:
        logger.warning("Invalid TopicArn: %s", message["TopicArn"])
        return False

    # Construct the canonical message
    if message["Type"] == "Notification":
        signing_keys = SIGNING_KEYS_NOTIFICATION
    elif message["Type"] in ("SubscriptionConfirmation", "UnsubscribeConfirmation"):
        signing_keys = SIGNING_KEYS_SUBSCRIPTION
    else:
        logger.warning("Invalid message type: %s", message["Type"])
        return False
    canonical_message = "".join(f"{key}\n{message[key]}\n" for key in signing_keys if key in message).encode()

    # Check if SigningCertURL is a valid SNS URL
    signing_cert_url = message["SigningCertURL"]
    parsed_url = urlparse(signing_cert_url)
    if (
        parsed_url.scheme != "https"
        or not HOST_PATTERN.match(parsed_url.netloc)
        or not parsed_url.path.endswith(".pem")
    ):
        logger.warning("Invalid SigningCertURL: %s", signing_cert_url)
        return False

    # Fetch the certificate
    certificate_bytes = fetch_certificate(signing_cert_url)

    # Verify the certificate issuer
    certificate = load_pem_x509_certificate(certificate_bytes)
    if certificate.issuer.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value != "Amazon":
        logger.warning("Invalid certificate issuer: %s", certificate.issuer)
        return False

    # Verify the signature
    signature = b64decode(message["Signature"])
    if message["SignatureVersion"] == "1":
        hash_algorithm = SHA1()
    elif message["SignatureVersion"] == "2":
        hash_algorithm = SHA256()
    else:
        logger.warning("Invalid SignatureVersion: %s", message["SignatureVersion"])
        return False
    try:
        certificate.public_key().verify(signature, canonical_message, PKCS1v15(), hash_algorithm)
    except InvalidSignature:
        logger.warning("Invalid signature")
        return False

    return True


def fetch_certificate(certificate_url: str) -> bytes:
    cache_key = f"aws_sns_cert_{certificate_url}"
    cached_certificate = cache.get(cache_key)
    if cached_certificate:
        return cached_certificate

    response = requests.get(certificate_url, timeout=5)
    response.raise_for_status()
    certificate = response.content

    cache.set(cache_key, certificate, timeout=60 * 60)  # Cache for 1 hour
    return certificate
