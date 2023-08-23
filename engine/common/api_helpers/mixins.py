import json
import math
import typing

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.utils.functional import cached_property
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, Throttled
from rest_framework.request import Request
from rest_framework.response import Response

from apps.alerts.incident_appearance.templaters import (
    AlertPhoneCallTemplater,
    AlertSlackTemplater,
    AlertSmsTemplater,
    AlertTelegramTemplater,
    AlertWebTemplater,
    TemplateLoader,
)
from apps.api.permissions import LegacyAccessControlRole
from apps.base.messaging import get_messaging_backends
from common.api_helpers.exceptions import BadRequest
from common.jinja_templater import apply_jinja_template
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning

X_INSTANCE_CONTEXT = "X-Instance-Context"

X_GRAFANA_CONTEXT = "X-Grafana-Context"


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


_MT = typing.TypeVar("_MT", bound=models.Model)


class PublicPrimaryKeyMixin(typing.Generic[_MT]):
    def get_object(self) -> _MT:
        pk = self.kwargs["pk"]
        queryset = self.filter_queryset(self.get_queryset())

        try:
            obj = queryset.get(public_primary_key=pk)
        except ObjectDoesNotExist:
            raise NotFound

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj


class TeamFilteringMixin:
    """
    This mixin returns 403 and {"error_code": "wrong_team", "owner_team": {"name", "id", "email", "avatar_url"}}
    in case a requested instance doesn't belong to user's current_team.
    """

    TEAM_LOOKUP = "team"

    @property
    def available_teams_lookup_args(self):
        """
        This property returns a list of Q objects that are used to filter instances by teams available to the user.
        NOTE: use .distinct() after filtering by available teams as it may return duplicate instances.
        """
        available_teams_lookup_args = []
        if not self.request.user.role == LegacyAccessControlRole.ADMIN:
            available_teams_lookup_args = [
                Q(**{f"{self.TEAM_LOOKUP}__users": self.request.user})
                | Q(**{f"{self.TEAM_LOOKUP}__is_sharing_resources_to_all": True})
                | Q(**{f"{self.TEAM_LOOKUP}__isnull": True})
            ]
        return available_teams_lookup_args

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except NotFound:
            queryset = self.filter_queryset(self.get_queryset(ignore_filtering_by_available_teams=True))
            try:
                queryset.get(public_primary_key=self.kwargs["pk"])
            except ObjectDoesNotExist:
                raise NotFound
            return Response(data={"error_code": "wrong_team"}, status=status.HTTP_403_FORBIDDEN)

    @staticmethod
    def _getattr_with_related(obj, lookup):
        entries = lookup.split("__")

        result = getattr(obj, entries[0])
        for entry in entries[1:]:
            result = getattr(result, entry)

        return result

    @staticmethod
    def _remove_filter(lookup, queryset):
        """
        This method removes a lookup from queryset.
        E.g. for queryset = Instance.objects.filter(a=5, team=None), _remove_filter("team", queryset) will modify the
        queryset to Instance.objects.filter(a=5).
        """
        query = queryset.query
        q = Q(**{lookup: None})
        clause, _ = query._add_q(q, query.used_aliases)

        def filter_lookups(child):
            try:
                return child.lhs.target != clause.children[0].lhs.target
            except AttributeError:
                return child.children[0].lhs.target != clause.children[0].lhs.target

        query.where.children = list(filter(filter_lookups, query.where.children))


# TODO: move to separate file
SLACK = "slack"
WEB = "web"
PHONE_CALL = "phone_call"
SMS = "sms"
TELEGRAM = "telegram"
# templates with its own field in db, this concept replaced by messaging_backend_templates field
NOTIFICATION_CHANNEL_OPTIONS = [SLACK, WEB, PHONE_CALL, SMS, TELEGRAM]

TITLE = "title"
MESSAGE = "message"
IMAGE_URL = "image_url"
RESOLVE_CONDITION = "resolve_condition"
ACKNOWLEDGE_CONDITION = "acknowledge_condition"
GROUPING_ID = "grouping_id"
SOURCE_LINK = "source_link"
ROUTE = "route"

NOTIFICATION_CHANNEL_TO_TEMPLATER_MAP = {
    SLACK: AlertSlackTemplater,
    WEB: AlertWebTemplater,
    PHONE_CALL: AlertPhoneCallTemplater,
    SMS: AlertSmsTemplater,
    TELEGRAM: AlertTelegramTemplater,
}

# add additionally supported messaging backends
for backend_id, backend in get_messaging_backends():
    if backend.templater is not None:
        NOTIFICATION_CHANNEL_OPTIONS.append(backend.slug)
        NOTIFICATION_CHANNEL_TO_TEMPLATER_MAP[backend.slug] = backend.get_templater_class()

APPEARANCE_TEMPLATE_NAMES = [TITLE, MESSAGE, IMAGE_URL]
BEHAVIOUR_TEMPLATE_NAMES = [RESOLVE_CONDITION, ACKNOWLEDGE_CONDITION, GROUPING_ID, SOURCE_LINK]
ROUTE_TEMPLATE_NAMES = [ROUTE]
ALL_TEMPLATE_NAMES = APPEARANCE_TEMPLATE_NAMES + BEHAVIOUR_TEMPLATE_NAMES + ROUTE_TEMPLATE_NAMES


class PreviewTemplateException(Exception):
    pass


class PreviewTemplateMixin:
    @action(methods=["post"], detail=True)
    def preview_template(self, request, pk):
        template_body = request.data.get("template_body", None)
        template_name = request.data.get("template_name", None)
        payload = request.data.get("payload", None)

        try:
            alert_to_template = self.get_alert_to_template(payload=payload)
            if alert_to_template is None:
                raise BadRequest(detail="Alert to preview does not exist")
        except PreviewTemplateException as e:
            raise BadRequest(detail=str(e))

        if template_body is None or template_name is None:
            response = {"preview": None}
            return Response(response, status=status.HTTP_200_OK)

        notification_channel, attr_name = self.parse_name_and_notification_channel(template_name)
        if attr_name is None:
            raise BadRequest(detail={"template_name": "Template name is missing"})
        if attr_name not in ALL_TEMPLATE_NAMES:
            raise BadRequest(detail={"template_name": "Unknown template name"})
        if attr_name in APPEARANCE_TEMPLATE_NAMES:
            if notification_channel is None:
                raise BadRequest(detail={"notification_channel": "notification_channel is required"})
            if notification_channel not in NOTIFICATION_CHANNEL_OPTIONS:
                raise BadRequest(detail={"notification_channel": "Unknown notification_channel"})

        if attr_name in APPEARANCE_TEMPLATE_NAMES:

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
            except (JinjaTemplateError, JinjaTemplateWarning) as e:
                return Response({"preview": e.fallback_message}, status.HTTP_200_OK)

            templated_attr = getattr(templated_alert, attr_name)

        elif attr_name in BEHAVIOUR_TEMPLATE_NAMES:
            try:
                templated_attr = apply_jinja_template(template_body, payload=alert_to_template.raw_request_data)
            except (JinjaTemplateError, JinjaTemplateWarning) as e:
                return Response({"preview": e.fallback_message}, status.HTTP_200_OK)
        elif attr_name in ROUTE_TEMPLATE_NAMES:
            try:
                templated_attr = apply_jinja_template(template_body, payload=alert_to_template.raw_request_data)
            except (JinjaTemplateError, JinjaTemplateWarning) as e:
                return Response({"preview": e.fallback_message}, status.HTTP_200_OK)
        else:
            templated_attr = None
        response = {"preview": templated_attr}
        return Response(response, status=status.HTTP_200_OK)

    def get_alert_to_template(self, payload=None):
        raise NotImplementedError

    @staticmethod
    def parse_name_and_notification_channel(template_param):
        template_param = template_param.replace("_template", "")
        attr_name = None
        destination = None
        if template_param.startswith(tuple(BEHAVIOUR_TEMPLATE_NAMES)):
            attr_name = template_param
        if template_param.startswith(tuple(ROUTE_TEMPLATE_NAMES)):
            attr_name = template_param
        elif template_param.startswith(tuple(NOTIFICATION_CHANNEL_OPTIONS)):
            for notification_channel in NOTIFICATION_CHANNEL_OPTIONS:
                if template_param.startswith(notification_channel):
                    destination = notification_channel
                    attr_name = template_param[len(destination) + 1 :]
                    break
        return destination, attr_name


class GrafanaContext(typing.TypedDict):
    IsAnonymous: bool


class InstanceContext(typing.TypedDict):
    stack_id: int
    org_id: int
    grafana_token: str


class GrafanaHeadersMixin:
    request: Request

    @cached_property
    def grafana_context(self) -> GrafanaContext:
        if X_GRAFANA_CONTEXT in self.request.headers:
            grafana_context: GrafanaContext = json.loads(self.request.headers[X_GRAFANA_CONTEXT])
        else:
            grafana_context = None
        return grafana_context

    @cached_property
    def instance_context(self) -> InstanceContext:
        if X_INSTANCE_CONTEXT in self.request.headers:
            instance_context: InstanceContext = json.loads(self.request.headers[X_INSTANCE_CONTEXT])
        else:
            instance_context = None
        return instance_context
