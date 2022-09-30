from .prod_without_db import *  # noqa: F403

MIRAGE_SECRET_KEY = SECRET_KEY  # noqa: F405
MIRAGE_CIPHER_IV = "1234567890abcdef"  # use default

APPEND_SLASH = False
SECURE_SSL_REDIRECT = False
