# flake8: noqa: F405

from .prod_without_db import *

MIRAGE_SECRET_KEY = SECRET_KEY
MIRAGE_CIPHER_IV = "1234567890abcdef"  # use default

APPEND_SLASH = False
SECURE_SSL_REDIRECT = False
