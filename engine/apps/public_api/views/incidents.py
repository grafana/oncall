from django.apps import apps
from django_filters import rest_framework as filters
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ViewSet

from apps.alerts.constants import ActionSource
from apps.alerts.models import AlertGroup
from apps.alerts.tasks import delete_alert_group, wipe
from apps.auth_token.auth import ApiTokenAuthentication
from apps.base.models import UserNotificationPolicyLogRecord
from apps.public_api.constants import VALID_DATE_FOR_DELETE_INCIDENT
from apps.public_api.helpers import is_valid_group_creation_date, team_has_slack_token_for_deleting
from apps.public_api.serializers import IncidentSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.filters import ByTeamModelFieldFilterMixin, get_team_queryset
from common.api_helpers.mixins import RateLimitHeadersMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class IncidentByTeamFilter(ByTeamModelFieldFilterMixin, filters.FilterSet):
    team = filters.ModelChoiceFilter(
        field_name="channel__team",
        queryset=get_team_queryset,
        to_field_name="public_primary_key",
        null_label="noteam",
        null_value="null",
        method=ByTeamModelFieldFilterMixin.filter_model_field_with_single_value.__name__,
    )


class IncidentView(
    RateLimitHeadersMixin, mixins.ListModelMixin, mixins.DestroyModelMixin, mixins.UpdateModelMixin, GenericViewSet
):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = AlertGroup
    serializer_class = IncidentSerializer
    pagination_class = FiftyPageSizePaginator

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = IncidentByTeamFilter

    def get_queryset(self):
        route_id = self.request.query_params.get("route_id", None)
        integration_id = self.request.query_params.get("integration_id", None)

        queryset = AlertGroup.unarchived_objects.filter(
            channel__organization=self.request.auth.organization,
        ).order_by("-started_at")

        if route_id:
            queryset = queryset.filter(channel_filter__public_primary_key=route_id)
        if integration_id:
            queryset = queryset.filter(channel__public_primary_key=integration_id)

        queryset = self.serializer_class.setup_eager_loading(queryset)

        return queryset

    def get_object(self):
        public_primary_key = self.kwargs["pk"]

        try:
            return AlertGroup.unarchived_objects.filter(
                channel__organization=self.request.auth.organization,
            ).get(public_primary_key=public_primary_key)
        except AlertGroup.DoesNotExist:
            raise NotFound

    def __get_user_by_email(self, email):
        User = apps.get_model("user_management", "User")
        try:
            user = User.objects.get(email=email)
            return user
        except User.DoesNotExist:
            raise NotFound(detail=f"user with email {email} not found")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not isinstance(request.data, dict):
            return Response(data="A dict with a `mode` key is expected", status=status.HTTP_400_BAD_REQUEST)
        mode = request.data.get("mode")
        if mode == "delete":
            if not team_has_slack_token_for_deleting(instance):
                raise BadRequest(
                    detail="Your OnCall Bot in Slack is outdated. Please reinstall OnCall Bot and try again."
                )
            elif not is_valid_group_creation_date(instance):
                raise BadRequest(
                    detail=f"We are unable to “delete” old alert_groups (created before "
                    f"{VALID_DATE_FOR_DELETE_INCIDENT.strftime('%d %B %Y')}) using API. "
                    f"Please use “wipe” mode or contact help. Sorry for that!"
                )
            else:
                delete_alert_group.apply_async((instance.pk, request.user.pk))
        else:
            wipe.apply_async((instance.pk, request.user.pk))

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["post"], detail=True)
    def acknowledge(self, request, pk):
        user_email = request.query_params.get("user_email", None)
        if not user_email:
            raise BadRequest(detail="missing 'user_email' query param")

        user = self.__get_user_by_email(email=user_email)
        alert_group = self.get_object()

        if alert_group.is_maintenance_incident:
            raise BadRequest(detail=f"Can't acknowledge maintenance alert group {pk}")
        if alert_group.root_alert_group is not None:
            raise BadRequest(detail=f"Can't acknowledge an attached alert group {pk}")
        if alert_group.acknowledged:
            raise BadRequest(detail=f"The alert group {pk} already acknowledged")

        alert_group.acknowledge_by_user(user, action_source=ActionSource.WEB)
        return Response(status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def unacknowledge(self, request, pk):
        user_email = request.query_params.get("user_email", None)
        if not user_email:
            raise BadRequest(detail="missing 'user_email' query param")

        user = self.__get_user_by_email(email=user_email)
        alert_group = self.get_object()

        if alert_group.is_maintenance_incident:
            raise BadRequest(detail=f"Can't unacknowledge maintenance alert group {pk}")
        if alert_group.root_alert_group is not None:
            raise BadRequest(detail=f"Can't unacknowledge an attached alert group {pk}")
        if alert_group.resolved:
            raise BadRequest(detail=f"Can't unacknowledge a resolved alert group {pk}")
        if not alert_group.acknowledged:
            raise BadRequest(detail=f"The alert group {pk} is not acknowledged")
        alert_group.un_acknowledge_by_user(user, action_source=ActionSource.WEB)
        return Response(status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def log(self, request, **_):
        user_email = request.query_params.get("user_email", None)
        if not user_email:
            raise BadRequest(detail="missing 'user_email' query param")

        user = self.__get_user_by_email(email=user_email)
        alert_group = self.get_object()

        user_notification_type = request.query_params.get("user_notification_type", None)
        if not user_notification_type:
            raise BadRequest(detail="missing 'user_notification_type' query param")

        notification_log_values = list(UserNotificationPolicyLogRecord.TYPE_TO_HANDLERS_MAP.values())

        # log is empty for finished type
        notification_log_values.remove("finished")
        if user_notification_type not in notification_log_values:
            raise BadRequest(
                detail=f"incorrect user_notification_type, allowed notification types: {notification_log_values}"
            )

        notification_error = None
        if user_notification_type == "failed":
            notification_error = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_CALL

        notification_types = dict(map(reversed, UserNotificationPolicyLogRecord.TYPE_TO_HANDLERS_MAP.items()))

        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=notification_types[user_notification_type],
            alert_group=alert_group,
            notification_error_code=notification_error,
        )

        return Response(status=status.HTTP_201_CREATED)