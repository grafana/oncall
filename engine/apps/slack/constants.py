import datetime

from apps.slack.types import Block

SLACK_BOT_ID = "USLACKBOT"
SLACK_INVALID_AUTH_RESPONSE = "no_enough_permissions_to_retrieve"
PLACEHOLDER = "Placeholder"

SLACK_WRONG_TEAM_NAMES = [SLACK_INVALID_AUTH_RESPONSE, PLACEHOLDER]

SLACK_RATE_LIMIT_TIMEOUT = datetime.timedelta(minutes=5)
SLACK_RATE_LIMIT_DELAY = 10
CACHE_UPDATE_INCIDENT_SLACK_MESSAGE_LIFETIME = 60 * 10

PRIVATE_METADATA_MAX_LENGTH = 3000

DIVIDER: Block.Divider = {"type": "divider"}
