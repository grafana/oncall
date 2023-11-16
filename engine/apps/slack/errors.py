import typing

from slack_sdk.web import SlackResponse

from apps.slack.constants import SLACK_RATE_LIMIT_DELAY


class UnexpectedResponse(typing.TypedDict):
    status: int
    headers: dict[str, typing.Any]
    body: str


class SlackAPIError(Exception):
    """
    Base class for Slack API errors. To add a new error class, add a new subclass of SlackAPIError in this file.
    See get_error_class at the end of this file for more details on how these are raised.
    """

    errors: tuple[str, ...]

    def __init__(self, response: UnexpectedResponse | SlackResponse):
        super().__init__(f"Slack API error! Response: {response}")
        self.response = response


class SlackAPIServerError(SlackAPIError):
    errors = ("internal_error", "fatal_error")


class SlackAPITokenError(SlackAPIError):
    errors = ("account_inactive", "token_revoked")


class SlackAPIChannelArchivedError(SlackAPIError):
    errors = ("is_archived",)


class SlackAPIRatelimitError(SlackAPIError):
    errors = ("ratelimited", "rate_limited", "message_limit_exceeded")

    def __init__(self, response: SlackResponse):
        super().__init__(response)
        self.retry_after = int(response.headers.get("Retry-After", SLACK_RATE_LIMIT_DELAY))


class SlackAPIPlanUpgradeRequiredError(SlackAPIError):
    errors = ("plan_upgrade_required",)


class SlackAPIInvalidAuthError(SlackAPIError):
    errors = ("invalid_auth",)


class SlackAPIUsergroupNotFoundError(SlackAPIError):
    errors = ("no_such_subteam", "subteam_not_found")


class SlackAPIInvalidUsersError(SlackAPIError):
    errors = ("invalid_users",)


class SlackAPIChannelNotFoundError(SlackAPIError):
    errors = ("channel_not_found",)


class SlackAPIMessageNotFoundError(SlackAPIError):
    errors = ("message_not_found",)


class SlackAPIUserNotFoundError(SlackAPIError):
    errors = ("user_not_found",)


class SlackAPIChannelInactiveError(SlackAPIError):
    errors = ("is_inactive",)


class SlackAPIRestrictedActionError(SlackAPIError):
    errors = ("restricted_action",)


class SlackAPIPermissionDeniedError(SlackAPIError):
    errors = ("permission_denied",)


class SlackAPIFetchMembersFailedError(SlackAPIError):
    errors = ("fetch_members_failed",)


class SlackAPIViewNotFoundError(SlackAPIError):
    errors = ("not_found",)


class SlackAPICannotDMBotError(SlackAPIError):
    errors = ("cannot_dm_bot",)


class SlackAPIMethodNotSupportedForChannelTypeError(SlackAPIError):
    errors = ("method_not_supported_for_channel_type",)


_error_to_error_class = {
    error: error_class for error_class in SlackAPIError.__subclasses__() for error in error_class.errors
}


def get_error_class(response: UnexpectedResponse | SlackResponse) -> typing.Type[SlackAPIError]:
    """Get an appropriate error class for the response"""

    if isinstance(response, dict):  # UnexpectedResponse
        return SlackAPIServerError

    return _error_to_error_class.get(response["error"], SlackAPIError)
