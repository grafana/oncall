import datetime
import logging

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestTimeLoggingMiddleware(MiddlewareMixin):
    @staticmethod
    def log_message(request, response, tag, message=""):
        dt = datetime.datetime.utcnow()
        if not hasattr(request, "_logging_start_dt"):
            request._logging_start_dt = dt
            if request.path.startswith("/integrations/v1"):
                logging.info(f"Start calculating latency for {request.path}")
        else:
            seconds = (dt - request._logging_start_dt).total_seconds()
            status_code = 0 if response is None else response.status_code
            content_length = request.headers.get("content-length", default=0)
            user_agent = request.META.get("HTTP_USER_AGENT", "unknown")
            message = (
                "inbound "
                f"latency={str(seconds)} status={status_code} method={request.method} path={request.path} "
                f"user_agent={user_agent} content-length={content_length} "
                f"slow={int(seconds > settings.SLOW_THRESHOLD_SECONDS)} "
            )
            if hasattr(request, "user") and request.user and request.user.id and hasattr(request.user, "organization"):
                user_id = request.user.id
                org_id = request.user.organization.id
                org_slug = request.user.organization.org_slug
                message += f"user_id={user_id} org_id={org_id} org_slug={org_slug} "
            if request.path.startswith("/integrations/v1"):
                split_path = request.path.split("/")
                integration_type = split_path[3]

                # integration token is not always present in the URL,
                # e.g. for inbound emails integration token is passed in the request payload
                if len(split_path) >= 5:
                    integration_token = split_path[4]
                else:
                    integration_token = None

                message += f"integration_type={integration_type} integration_token={integration_token} "
            logging.info(message)

    def process_request(self, request):
        self.log_message(request, None, "request")

    def process_response(self, request, response):
        self.log_message(request, response, "response")
        return response


class LogRequestHeadersMiddleware:
    """
    Middleware to log the request headers.
    Introduced to debug tracing issues.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request headers
        logger.info("Request Headers: %s", request.headers)

        response = self.get_response(request)

        return response
