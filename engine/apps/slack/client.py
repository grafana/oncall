import logging
from typing import Optional, Tuple

from django.utils import timezone
from rest_framework import status
from slack_sdk.errors import SlackApiError as SlackSDKApiError
from slack_sdk.http_retry import HttpRequest, HttpResponse, RetryHandler, RetryState, default_retry_handlers
from slack_sdk.web import SlackResponse, WebClient

from apps.slack.errors import (
    SlackAPIError,
    SlackAPIRatelimitError,
    SlackAPIServerError,
    SlackAPITokenError,
    UnexpectedResponse,
)

logger = logging.getLogger(__name__)


class SlackServerErrorRetryHandler(RetryHandler):
    def _can_retry(
        self,
        *,
        state: RetryState,
        request: HttpRequest,
        response: Optional[HttpResponse] = None,
        error: Optional[Exception] = None,
    ) -> bool:
        if response and response.body and response.body.get("error") in SlackAPIServerError.errors:
            return True

        if response and response.status_code in [
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_504_GATEWAY_TIMEOUT,
        ]:
            return True

        return False


server_error_retry_handler = SlackServerErrorRetryHandler(max_retry_count=2)


class SlackClientWithErrorHandling(WebClient):
    def __init__(self, slack_team_identity, timeout: int = 30):
        super().__init__(
            token=slack_team_identity.bot_access_token,
            timeout=timeout,
            retry_handlers=default_retry_handlers() + [server_error_retry_handler],
        )
        self.slack_team_identity = slack_team_identity

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

        except SlackAPIRatelimitError:
            rate_limited = True

        return cumulative_response, cursor, rate_limited

    def api_call(self, *args, **kwargs):
        try:
            response = super().api_call(*args, **kwargs)
            self._unmark_token_revoked()  # unmark token as revoked if the API call was successful
            return response
        except SlackSDKApiError as e:
            logger.error(
                "Slack API error! args={} kwargs={} status={} error={} response={}".format(
                    args,
                    kwargs,
                    e.response["status"] if isinstance(e.response, dict) else e.response.status_code,
                    e.response.get("error"),
                    e.response,
                )
            )

            # narrow down the error
            error_class = self._get_error_class(e.response)

            # mark / unmark token as revoked
            if error_class is SlackAPITokenError:
                self._mark_token_revoked()
            else:
                self._unmark_token_revoked()

            # raise the narrowed down error class
            raise error_class(e.response) from e

    @staticmethod
    def _get_error_class(response: UnexpectedResponse | SlackResponse):
        if isinstance(response, dict):  # UnexpectedResponse
            return SlackAPIServerError

        for error_class in SlackAPIError.__subclasses__():
            if response["error"] in error_class.errors:
                return error_class

        return SlackAPIError

    def _mark_token_revoked(self):
        if not self.slack_team_identity.detected_token_revoked:
            self.slack_team_identity.detected_token_revoked = timezone.now()
            self.slack_team_identity.save(update_fields=["detected_token_revoked"])

    def _unmark_token_revoked(self):
        if self.slack_team_identity.detected_token_revoked:
            self.slack_team_identity.detected_token_revoked = None
            self.slack_team_identity.save(update_fields=["detected_token_revoked"])
