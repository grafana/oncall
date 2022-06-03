import json
import math

from django.core.exceptions import ObjectDoesNotExist
from django.utils.functional import cached_property
from jinja2.exceptions import TemplateRuntimeError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, Throttled
from rest_framework.response import Response

from apps.alerts.incident_appearance.templaters import (
    AlertEmailTemplater,
    AlertPhoneCallTemplater,
    AlertSlackTemplater,
    AlertSmsTemplater,
    AlertTelegramTemplater,
    AlertWebTemplater,
    TemplateLoader,
)
from apps.base.messaging import get_messaging_backends
from apps.public_api.helpers import is_demo_token_request
from common.api_helpers.exceptions import BadRequest
from common.jinja_templater import apply_jinja_template


class UpdateSerializerMixin:
    serializer_class = None
    update_serializer_class = None

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return self.get_update_serializer_class()
        return super().get_serializer_class()

    def get_update_serializer_class(self):
        assert self.update_serializer_class is not None, (
            "'%s' should either include a `update_serializer_class` attribute,"
            "or override the `get_update_serializer_class()` method." % self.__class__.__name__
        )
        return self.update_serializer_class


# Use this mixin at the very left of list of inherited SerializersMixins
class FilterSerializerMixin:
    serializer_class = None
    filter_serializer_class = None

    def get_serializer_class(self):
        is_filters_request = self.request.query_params.get("filters", "false") == "true"
        if self.action in ["list"] and is_filters_request:
            return self.get_filter_serializer_class()
        else:
            return super().get_serializer_class()

    def get_filter_serializer_class(self):
        assert self.filter_serializer_class is not None, (
            "'%s' should either include a `filter_serializer_class` attribute,"
            "or override the `get_update_serializer_class()` method." % self.__class__.__name__
        )
        return self.filter_serializer_class


# Use this mixin at the very left of list of inherited SerializersMixins
class ShortSerializerMixin:
    serializer_class = None
    short_serializer_class = None

    def get_serializer_class(self):
        is_short_request = self.request.query_params.get("short", "false") == "true"
        if self.action in ["list"] and is_short_request:
            return self.get_short_serializer_class()
        else:
            return super().get_serializer_class()

    def get_short_serializer_class(self):
        assert self.short_serializer_class is not None, (
            "'%s' should either include a `short_serializer_class` attribute,"
            "or override the `get_list_serializer_class()` method." % self.__class__.__name__
        )
        return self.short_serializer_class


class CreateSerializerMixin:
    serializer_class = None
    create_serializer_class = None

    def get_serializer_class(self):
        if self.action in ["create", "destroy"]:
            return self.get_create_serializer_class()
        return super().get_serializer_class()

    def get_create_serializer_class(self):
        assert self.create_serializer_class is not None, (
            "'%s' should either include a `create_serializer_class` attribute,"
            "or override the `get_update_serializer_class()` method." % self.__class__.__name__
        )
        return self.create_serializer_class


class ListSerializerMixin:
    serializer_class = None
    list_serializer_class = None

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return self.get_list_serializer_class()
        return super().get_serializer_class()

    def get_list_serializer_class(self):
        assert self.list_serializer_class is not None, (
            "'%s' should either include a `list_serializer_class` attribute,"
            "or override the `get_list_serializer_class()` method." % self.__class__.__name__
        )
        return self.list_serializer_class


class EagerLoadingMixin:
    @classmethod
    def setup_eager_loading(cls, queryset):
        if hasattr(cls, "SELECT_RELATED"):
            queryset = queryset.select_related(*cls.SELECT_RELATED)
        if hasattr(cls, "PREFETCH_RELATED"):
            queryset = queryset.prefetch_related(*cls.PREFETCH_RELATED)
        return queryset


class DemoTokenMixin:
    """
    The view mixin for requests to public api with demo token authorization.
    """

    def dispatch(self, request, *args, **kwargs):
        """
        Overridden dispatch method of APIView
        https://github.com/encode/django-rest-framework/blob/master/rest_framework/views.py#L485
        """
        method = request.method.lower()

        if is_demo_token_request(request) and method in ["post", "put", "delete"]:
            self.args = args
            self.kwargs = kwargs
            request = self.initialize_request(request, *args, **kwargs)
            self.request = request

            # there is a strange comment about this
            # https://github.com/encode/django-rest-framework/blob/master/rest_framework/views.py#L494
            self.headers = self.default_response_headers

            try:
                self.initial(request, *args, **kwargs)

                """
                check for allowed request methods

                from APIView:
                If `request.method` does not correspond to a handler method,
                determine what kind of exception to raise.

                def http_method_not_allowed(self, request, *args, **kwargs):
                    raise exceptions.MethodNotAllowed(request.method)
                """

                if method in self.http_method_names:
                    handler = getattr(self, method, self.http_method_not_allowed)
                else:
                    handler = self.http_method_not_allowed

                # function comparison explanation
                # https://stackoverflow.com/a/18217024
                if handler == self.http_method_not_allowed:
                    response = handler(request, *args, **kwargs)

                elif method == "post":
                    # It excludes a real instance creation.
                    # It returns the instance with public primary key
                    # is equal to demo_default_id
                    instance = self.model._default_manager.get(public_primary_key=self.demo_default_id)
                    serializer = self.get_serializer(instance)
                    headers = self.get_success_headers(serializer.data)
                    response = Response(data=serializer.data, status=status.HTTP_201_CREATED, headers=headers)

                elif method == "put":
                    # It excludes a instance update.
                    # It returns the instance with public primary key
                    # is equal to demo_default_id
                    instance = self.get_object()
                    serializer = self.get_serializer(instance)
                    headers = self.get_success_headers(serializer.data)
                    response = Response(data=serializer.data, status=status.HTTP_200_OK, headers=headers)

                elif method == "delete":
                    # In this case we return nothing just success response.
                    response = Response(status=status.HTTP_204_NO_CONTENT)

            except Exception as exc:
                response = self.handle_exception(exc)

            self.response = self.finalize_response(request, response, *args, **kwargs)
            return self.response

        return super().dispatch(request, *args, **kwargs)


class RateLimitHeadersMixin:
    # This mixin add RateLimit-Reset header to RateLimited response
    def handle_exception(self, exc):
        if isinstance(exc, Throttled):
            if exc.wait is not None:
                wait = f"{math.ceil(exc.wait)}"
            else:
                # if wait is none use maximum wait delay.
                # This case can be reproduced if decrease ratelimit when self.history is not empty
                wait = f"{350}"
            self.headers["RateLimit-Reset"] = wait
        return super().handle_exception(exc)


class OrderedModelSerializerMixin:
    def _change_position(self, order, instance):
        if order is not None:
            if order >= 0:
                instance.to(order)
            elif order == -1:
                instance.bottom()
            else:
                raise BadRequest(detail="Invalid value for position field")

    def _validate_order(self, order, filter_kwargs):
        if order is not None and (self.instance is None or self.instance.order != order):
            last_instance = self.Meta.model.objects.filter(**filter_kwargs).order_by("order").last()
            max_order = last_instance.order if last_instance else -1
            if self.instance is None:
                max_order += 1
            if order > max_order:
                raise BadRequest(detail="Invalid value for position field")


class PublicPrimaryKeyMixin:
    def get_object(self):
        pk = self.kwargs["pk"]
        queryset = self.filter_queryset(self.get_queryset())

        try:
            obj = queryset.get(public_primary_key=pk)
        except ObjectDoesNotExist:
            raise NotFound

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj


# TODO: move to separate file
SLACK = "slack"
WEB = "web"
PHONE_CALL = "phone_call"
SMS = "sms"
EMAIL = "email"
TELEGRAM = "telegram"
NOTIFICATION_CHANNEL_OPTIONS = [SLACK, WEB, PHONE_CALL, SMS, EMAIL, TELEGRAM]
TITLE = "title"
MESSAGE = "message"
IMAGE_URL = "image_url"
RESOLVE_CONDITION = "resolve_condition"
ACKNOWLEDGE_CONDITION = "acknowledge_condition"
GROUPING_ID = "grouping_id"
SOURCE_LINK = "source_link"
TEMPLATE_NAME_OPTIONS = [TITLE, MESSAGE, IMAGE_URL, RESOLVE_CONDITION, ACKNOWLEDGE_CONDITION, GROUPING_ID, SOURCE_LINK]
NOTIFICATION_CHANNEL_TO_TEMPLATER_MAP = {
    SLACK: AlertSlackTemplater,
    WEB: AlertWebTemplater,
    PHONE_CALL: AlertPhoneCallTemplater,
    SMS: AlertSmsTemplater,
    EMAIL: AlertEmailTemplater,
    TELEGRAM: AlertTelegramTemplater,
}

# add additionally supported messaging backends
for backend_id, backend in get_messaging_backends():
    if backend.templater is not None:
        backend_slug = backend_id.lower()
        NOTIFICATION_CHANNEL_OPTIONS.append(backend_slug)
        NOTIFICATION_CHANNEL_TO_TEMPLATER_MAP[backend_slug] = backend.get_templater_class()

TEMPLATE_NAMES_ONLY_WITH_NOTIFICATION_CHANNEL = [TITLE, MESSAGE, IMAGE_URL]
TEMPLATE_NAMES_WITHOUT_NOTIFICATION_CHANNEL = [RESOLVE_CONDITION, ACKNOWLEDGE_CONDITION, GROUPING_ID, SOURCE_LINK]


class PreviewTemplateMixin:
    @action(methods=["post"], detail=True)
    def preview_template(self, request, pk):
        template_body = request.data.get("template_body", None)
        template_name = request.data.get("template_name", None)

        if template_body is None or template_name is None:
            response = {"preview": None}
            return Response(response, status=status.HTTP_200_OK)

        notification_channel, attr_name = self.parse_name_and_notification_channel(template_name)
        if attr_name is None:
            raise BadRequest(detail={"template_name": "Attr name is required"})
        if attr_name not in TEMPLATE_NAME_OPTIONS:
            raise BadRequest(detail={"template_name": "Unknown attr name"})
        if attr_name in TEMPLATE_NAMES_ONLY_WITH_NOTIFICATION_CHANNEL:
            if notification_channel is None:
                raise BadRequest(detail={"notification_channel": "notification_channel is required"})
            if notification_channel not in NOTIFICATION_CHANNEL_OPTIONS:
                raise BadRequest(detail={"notification_channel": "Unknown notification_channel"})

        alert_to_template = self.get_alert_to_template()
        if alert_to_template is None:
            raise BadRequest(detail="Alert to preview does not exist")

        if attr_name in TEMPLATE_NAMES_ONLY_WITH_NOTIFICATION_CHANNEL:

            class PreviewTemplateLoader(TemplateLoader):
                def get_attr_template(self, attr, alert_receive_channel, render_for=None):
                    if attr == attr_name and render_for == notification_channel:
                        return template_body
                    else:
                        return super().get_attr_template(attr, alert_receive_channel, render_for)

            templater_cls = NOTIFICATION_CHANNEL_TO_TEMPLATER_MAP[notification_channel]
            templater = templater_cls(alert_to_template)
            templater.template_manager = PreviewTemplateLoader()
            try:
                templated_alert = templater.render()
            except TemplateRuntimeError:
                raise BadRequest(detail={"template_body": "Invalid template syntax"})

            templated_attr = getattr(templated_alert, attr_name)

        elif attr_name in TEMPLATE_NAMES_WITHOUT_NOTIFICATION_CHANNEL:
            templated_attr, _ = apply_jinja_template(template_body, payload=alert_to_template.raw_request_data)
        else:
            templated_attr = None
        response = {"preview": templated_attr}
        return Response(response, status=status.HTTP_200_OK)

    def get_alert_to_template(self):
        raise NotImplementedError

    @staticmethod
    def parse_name_and_notification_channel(template_param):
        template_param = template_param.replace("_template", "")
        attr_name = None
        destination = None
        if template_param.startswith(tuple(TEMPLATE_NAMES_WITHOUT_NOTIFICATION_CHANNEL)):
            attr_name = template_param
        elif template_param.startswith(tuple(NOTIFICATION_CHANNEL_OPTIONS)):
            for notification_channel in NOTIFICATION_CHANNEL_OPTIONS:
                if template_param.startswith(notification_channel):
                    destination = notification_channel
                    attr_name = template_param[len(destination) + 1 :]
                    break
        return destination, attr_name


class GrafanaHeadersMixin:
    @cached_property
    def grafana_context(self) -> dict:
        return json.loads(self.request.headers.get("X-Grafana-Context"))

    @cached_property
    def instance_context(self) -> dict:
        return json.loads(self.request.headers["X-Instance-Context"])
