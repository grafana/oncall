AUTH_TOKEN_CHARACTER_LENGTH = 64
AUTH_SHORT_TOKEN_CHARACTER_LENGTH = 6
TOKEN_KEY_LENGTH = 8
DIGEST_LENGTH = 128
MAX_PUBLIC_API_TOKENS_PER_USER = 5

SLACK_AUTH_TOKEN_NAME = "slack_login_token"
GOOGLE_OAUTH2_AUTH_TOKEN_NAME = "state"
"""
We must use the `state` query param, otherwise Google returns a 400 error.

https://developers.google.com/identity/protocols/oauth2/web-server#:~:text=Specifies%20any%20string%20value%20that%20your%20application%20uses%20to%20maintain%20state%20between%20your%20authorization%20request%20and%20the%20authorization%20server%27s%20response
"""

SCHEDULE_EXPORT_TOKEN_NAME = "token"
SCHEDULE_EXPORT_TOKEN_CHARACTER_LENGTH = 32
