import logging
from typing import Optional, Tuple

from django.utils import timezone
from slackclient import SlackClient
from slackclient.exceptions import TokenRefreshError

from apps.slack.constants import SLACK_RATE_LIMIT_DELAY

from .exceptions import (
    SlackAPIChannelArchivedException,
    SlackAPIException,
    SlackAPIRateLimitException,
    SlackAPITokenException,
)
from .slack_client_server import SlackClientServer

logger = logging.getLogger(__name__)


class SlackClientWithErrorHandling(SlackClient):
    def __init__(self, token=None, **kwargs):
        """
        This method is rewritten because we want to use custom server SlackClientServer for SlackClient
        """
        super().__init__(token=token, **kwargs)

        proxies = kwargs.get("proxies")

        if self.refresh_token:
            if callable(self.token_update_callback):
                token = None
            else:
                raise TokenRefreshError("Token refresh callback function is required when using refresh token.")
        # Slack app configs
        self.server = SlackClientServer(token=token, connect=False, proxies=proxies)

    def paginated_api_call(self, *args, **kwargs):
        # It's a key from response which is paginated. For example "users" or "channels"
        listed_key = kwargs["paginated_key"]

        response = self.api_call(*args, **kwargs)
        cumulative_response = response

        while (
            "response_metadata" in response
            and "next_cursor" in response["response_metadata"]
            and response["response_metadata"]["next_cursor"] != ""
        ):
            kwargs["cursor"] = response["response_metadata"]["next_cursor"]
            response = self.api_call(*args, **kwargs)
            cumulative_response[listed_key] += response[listed_key]

        return cumulative_response

    def paginated_api_call_with_ratelimit(self, *args, **kwargs) -> Tuple[dict, Optional[str], bool]:
        """
        This method do paginated api call and handle slack rate limit error in order to return collected data and have
        ability to continue doing paginated requests from the last successful cursor. Return last successful cursor
        instead of next cursor to avoid data loss during delay time
        """
        # It's a key from response which is paginated. For example "users" or "channels"
        listed_key = kwargs["paginated_key"]
        cumulative_response = {}
        cursor = kwargs.get("cursor")
        rate_limited = False

        try:
            response = self.api_call(*args, **kwargs)
            cumulative_response = response
            cursor = response["response_metadata"]["next_cursor"]

            while (
                "response_metadata" in response
                and "next_cursor" in response["response_metadata"]
                and response["response_metadata"]["next_cursor"] != ""
            ):
                next_cursor = response["response_metadata"]["next_cursor"]
                kwargs["cursor"] = next_cursor
                response = self.api_call(*args, **kwargs)
                cumulative_response[listed_key] += response[listed_key]
                cursor = next_cursor

        except SlackAPIRateLimitException:
            rate_limited = True

        return cumulative_response, cursor, rate_limited

    def api_call(self, *args, **kwargs):
        response = super(SlackClientWithErrorHandling, self).api_call(*args, **kwargs)

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
