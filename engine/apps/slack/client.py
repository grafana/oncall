import logging
from typing import Optional, Tuple

from django.utils import timezone
from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient

from apps.slack.constants import SLACK_RATE_LIMIT_DELAY

logger = logging.getLogger(__name__)


class SlackAPIException(Exception):
    def __init__(self, *args, **kwargs):
        self.response = {}
        if "response" in kwargs:
            self.response = kwargs["response"]
        super().__init__(*args)


class SlackAPITokenException(SlackAPIException):
    pass


class SlackAPIChannelArchivedException(SlackAPIException):
    pass


class SlackAPIRateLimitException(SlackAPIException):
    pass


class SlackClientWithErrorHandling(WebClient):
    def paginated_api_call(self, method: str, paginated_key: str, **kwargs):
        """
        `paginated_key` represents a key from the response which is paginated. For example "users" or "channels"
        """
        api_method = getattr(self, method)

        response = api_method(**kwargs)
        cumulative_response = response.data

        while (
            "response_metadata" in response
            and "next_cursor" in response["response_metadata"]
            and response["response_metadata"]["next_cursor"] != ""
        ):
            kwargs["cursor"] = response["response_metadata"]["next_cursor"]
            response = api_method(**kwargs).data
            cumulative_response[paginated_key] += response[paginated_key]

        return cumulative_response

    def paginated_api_call_with_ratelimit(
        self, method: str, paginated_key: str, **kwargs
    ) -> Tuple[dict, Optional[str], bool]:
        """
        This method does paginated api calls and handle slack rate limit errors in order to return collected data
        and have the ability to continue doing paginated requests from the last successful cursor.

        Return last successful cursor instead of next cursor to avoid data loss during delay time.

        `paginated_key` represents a key from the response which is paginated. For example "users" or "channels"
        """
        api_method = getattr(self, method)

        cumulative_response = {}
        cursor = kwargs["cursor"]
        rate_limited = False

        try:
            response = api_method(**kwargs).data
            cumulative_response = response
            cursor = response["response_metadata"]["next_cursor"]

            while (
                "response_metadata" in response
                and "next_cursor" in response["response_metadata"]
                and response["response_metadata"]["next_cursor"] != ""
            ):
                next_cursor = response["response_metadata"]["next_cursor"]
                kwargs["cursor"] = next_cursor
                response = api_method(**kwargs).data
                cumulative_response[paginated_key] += response[paginated_key]
                cursor = next_cursor

        except SlackAPIRateLimitException:
            rate_limited = True

        return cumulative_response, cursor, rate_limited

    def api_call(self, *args, **kwargs):
        try:
            response = super(SlackClientWithErrorHandling, self).api_call(*args, **kwargs)
        except SlackApiError as err:
            response = err.response

        if not response["ok"]:
            exception_text = "Slack API Call Error: {} \nArgs: {} \nKwargs: {} \nResponse: {}".format(
                response["error"], args, kwargs, response
            )

            if response["error"] == "is_archived":
                raise SlackAPIChannelArchivedException(exception_text, response=response)

            if (
                response["error"] == "rate_limited"
                or response["error"] == "ratelimited"
                or response["error"] == "message_limit_exceeded"
                # "message_limit_exceeded" is related to the limit on post messages for free Slack workspace
            ):
                if "headers" in response and response["headers"].get("Retry-After") is not None:
                    delay = int(response["headers"]["Retry-After"])
                else:
                    delay = SLACK_RATE_LIMIT_DELAY
                response["rate_limit_delay"] = delay
                raise SlackAPIRateLimitException(exception_text, response=response)

            if response["error"] == "code_already_used":
                return response

            # Optionally detect account_inactive
            if response["error"] == "account_inactive" or response["error"] == "token_revoked":
                if "team" in kwargs:
                    team_identity = kwargs["team"]
                    del kwargs["team"]
                    team_identity.detected_token_revoked = timezone.now()
                    team_identity.is_profile_populated = False
                    team_identity.save(update_fields=["detected_token_revoked", "is_profile_populated"])
                raise SlackAPITokenException(exception_text, response=response)
            else:
                if "team" in kwargs:
                    slack_team_identity = kwargs["team"]
                    if slack_team_identity.detected_token_revoked:
                        slack_team_identity.detected_token_revoked = None
                        slack_team_identity.save(update_fields=["detected_token_revoked"])

            raise SlackAPIException(exception_text, response=response)

        return response
