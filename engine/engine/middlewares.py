import datetime
import logging

from django.apps import apps
from django.conf import settings
from django.core.exceptions import PermissionDenied, RequestDataTooBig
from django.db import OperationalError
from django.http import HttpResponse
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
            integration_type = "N/A"
            integration_token = "N/A"
            if request.path.startswith("/integrations/v1"):
                split_path = request.path.split("/")
                integration_type = split_path[3]
                integration_token = split_path[4]
            logging.info(
                "inbound "
                f"latency={str(seconds)} status={status_code} method={request.method} path={request.path} "
                f"content-length={content_length} slow={int(seconds > settings.SLOW_THRESHOLD_SECONDS)} "
                f"integration_type={integration_type} "
                f"integration_token={integration_token}"
            )

    def process_request(self, request):
        self.log_message(request, None, "request")

    def process_response(self, request, response):
        self.log_message(request, response, "response")
        return response


class RequestBodyReadingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Reading request body, as required by uwsgi
        # https://uwsgi-docs.readthedocs.io/en/latest/ThingsToKnow.html
        # "If an HTTP request has a body (like a POST request generated by a form),
        # you have to read (consume) it in your application.
        # If you do not do this, the communication socket with your webserver may be clobbered."
        try:
            request.body
        except RequestDataTooBig:
            return HttpResponse(status=400)


class BanAlertConsumptionBasedOnSettingsMiddleware(MiddlewareMixin):
    """
    Banning requests for /integrations/v1
    Banning is not guaranteed.
    """

    def is_banned(self, path):
        try:
            DynamicSetting = apps.get_model("base", "DynamicSetting")
            banned_paths = DynamicSetting.objects.get_or_create(
                name="ban_hammer_list",
                defaults={
                    "json_value": [
                        "full_path_here",
                    ]
                },
            )[0]
            result = any(p for p in banned_paths.json_value if path.startswith(p))
            return result
        except OperationalError:
            # Fallback to make sure we consume the request even if DB is down.
            logger.info("Cannot connect to database, assuming the request is not banned by default.")
            return False

    def process_request(self, request):
        if request.path.startswith("/integrations/v1") and self.is_banned(request.path):
            try:
                # Consume request body since other middleware will be skipped
                request.body
            except Exception:
                pass
            logging.warning(f"{request.path} has been banned")
            raise PermissionDenied()
