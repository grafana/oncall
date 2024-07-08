import typing

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Max, Q
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.alerts.constants import ActionSource
from apps.alerts.models import Alert, AlertGroup, AlertReceiveChannel, EscalationChain, ResolutionNote
from apps.alerts.paging import unpage_user
from apps.alerts.tasks import delete_alert_group, send_update_resolution_note_signal
from apps.api.errors import AlertGroupAPIError
from apps.api.label_filtering import parse_label_query
from apps.api.permissions import RBACPermission
from apps.api.serializers.alert_group import AlertGroupListSerializer, AlertGroupSerializer
from apps.api.serializers.alert_group_escalation_snapshot import AlertGroupEscalationSnapshotAPISerializer
from apps.api.serializers.team import TeamSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.base.models.user_notification_policy_log_record import UserNotificationPolicyLogRecord
from apps.labels.utils import is_labels_feature_enabled
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
from apps.user_management.models import Team, User
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.filters import (
    NO_TEAM_VALUE,
    DateRangeFilterMixin,
    ModelFieldFilterMixin,
    MultipleChoiceCharFilter,
)
from common.api_helpers.mixins import PreviewTemplateMixin, PublicPrimaryKeyMixin, TeamFilteringMixin
from common.api_helpers.paginators import AlertGroupCursorPaginator


def get_integration_queryset(request):
    if request is None:
        return AlertReceiveChannel.objects.none()

    return AlertReceiveChannel.objects_with_maintenance.filter(organization=request.user.organization)


def get_escalation_chain_queryset(request):
    if request is None:
        return EscalationChain.objects.none()

    return EscalationChain.objects.filter(organization=request.user.organization)


def get_user_queryset(request):
    if request is None:
        return User.objects.none()

    return User.objects.filter(organization=request.user.organization).distinct()


class AlertGroupFilter(DateRangeFilterMixin, ModelFieldFilterMixin, filters.FilterSet):
    """
    Examples of possible date formats here https://docs.djangoproject.com/en/1.9/ref/settings/#datetime-input-formats
    """

    FILTER_BY_INVOLVED_USERS_ALERT_GROUPS_CUTOFF = 1000

    is_root = filters.BooleanFilter(field_name="root_alert_group", lookup_expr="isnull")
    status = filters.MultipleChoiceFilter(choices=AlertGroup.STATUS_CHOICES, method="filter_status")
    started_at = filters.CharFilter(
        field_name="started_at",
        method=DateRangeFilterMixin.filter_date_range.__name__,
    )
    resolved_at = filters.CharFilter(
        field_name="resolved_at",
        method=DateRangeFilterMixin.filter_date_range.__name__,
    )
    integration = MultipleChoiceCharFilter(
        field_name="channel",
        queryset=get_integration_queryset,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )
    escalation_chain = MultipleChoiceCharFilter(
        field_name="channel_filter__escalation_chain",
        queryset=get_escalation_chain_queryset,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )
    resolved_by = MultipleChoiceCharFilter(
        field_name="resolved_by_user",
        queryset=get_user_queryset,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )
    acknowledged_by = MultipleChoiceCharFilter(
        field_name="acknowledged_by_user",
        queryset=get_user_queryset,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )
    silenced_by = MultipleChoiceCharFilter(
        field_name="silenced_by_user",
        queryset=get_user_queryset,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )
    invitees_are = MultipleChoiceCharFilter(
        queryset=get_user_queryset, to_field_name="public_primary_key", method="filter_invitees_are"
    )
    involved_users_are = MultipleChoiceCharFilter(
        queryset=get_user_queryset, to_field_name="public_primary_key", method="filter_by_involved_users"
    )
    with_resolution_note = filters.BooleanFilter(method="filter_with_resolution_note")
    mine = filters.BooleanFilter(method="filter_mine")

    def filter_status(self, queryset, name, value):
        if not value:
            return queryset
        try:
            statuses = list(map(int, value))
        except ValueError:
            raise BadRequest(detail="Invalid status value")

        filters = {}
        q_objects = Q()

        if AlertGroup.NEW in statuses:
            filters["new"] = AlertGroup.get_new_state_filter()
        if AlertGroup.SILENCED in statuses:
            filters["silenced"] = AlertGroup.get_silenced_state_filter()
        if AlertGroup.ACKNOWLEDGED in statuses:
            filters["acknowledged"] = AlertGroup.get_acknowledged_state_filter()
        if AlertGroup.RESOLVED in statuses:
            filters["resolved"] = AlertGroup.get_resolved_state_filter()

        for item in filters:
            q_objects |= filters[item]

        queryset = queryset.filter(q_objects)

        return queryset

    def filter_invitees_are(self, queryset, name, value):
        users = value

        if not users:
            return queryset

        queryset = queryset.filter(log_records__author__in=users).distinct()

        return queryset

    def filter_by_involved_users(self, queryset, name, value):
        users = value

        if not users:
            return queryset

        # This is expensive to filter all alert groups with involved users,
        # so we limit the number of alert groups to filter by the last 1000 for the given user(s)
        alert_group_notified_users_ids = list(
            UserNotificationPolicyLogRecord.objects.filter(author__in=users)
            .order_by("-alert_group_id")
            .values_list("alert_group_id", flat=True)
            .distinct()[: self.FILTER_BY_INVOLVED_USERS_ALERT_GROUPS_CUTOFF]
        )

        queryset = queryset.filter(
            # user was notified
            Q(id__in=alert_group_notified_users_ids)
            |
            # or interacted with the alert group
            Q(acknowledged_by_user__in=users)
            | Q(resolved_by_user__in=users)
            | Q(silenced_by_user__in=users)
        ).distinct()
        return queryset

    def filter_mine(self, queryset, name, value):
        if value:
            return self.filter_by_involved_users(queryset, "users", [self.request.user])
        return queryset

    def filter_with_resolution_note(self, queryset, name, value):
        if value is True:
            queryset = queryset.filter(Q(resolution_notes__isnull=False, resolution_notes__deleted_at=None)).distinct()
        elif value is False:
            queryset = queryset.filter(
                Q(resolution_notes__isnull=True) | ~Q(resolution_notes__deleted_at=None)
            ).distinct()
        return queryset


class AlertGroupTeamFilteringMixin(TeamFilteringMixin):
    TEAM_LOOKUP = "team"

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except NotFound:
            alert_receive_channels_ids = list(
                AlertReceiveChannel.objects.filter(
                    organization_id=self.request.auth.organization.id,
                ).values_list("id", flat=True)
            )
            queryset = AlertGroup.objects.filter(
                channel__in=alert_receive_channels_ids,
            ).only("public_primary_key")

            try:
                obj = queryset.get(public_primary_key=self.kwargs["pk"])
            except ObjectDoesNotExist:
                raise NotFound

            obj_team = self._getattr_with_related(obj, self.TEAM_LOOKUP)

            if obj_team is None or obj_team in self.request.user.teams.all():
                if obj_team is None:
                    obj_team = Team(public_primary_key=None, name="General", email=None, avatar_url=None)

                return Response(
                    data={"error_code": "wrong_team", "owner_team": TeamSerializer(obj_team).data},
                    status=status.HTTP_403_FORBIDDEN,
                )

            return Response(data={"error_code": "wrong_team"}, status=status.HTTP_403_FORBIDDEN)


class AlertGroupView(
    PreviewTemplateMixin,
    AlertGroupTeamFilteringMixin,
    PublicPrimaryKeyMixin[AlertGroup],
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Internal API endpoints for alert groups.
    """

    authentication_classes = (
        MobileAppAuthTokenAuthentication,
        PluginAuthentication,
    )
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "metadata": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "list": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "retrieve": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "stats": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "filters": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "silence_options": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "bulk_action_options": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "destroy": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "acknowledge": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "unacknowledge": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "resolve": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "unresolve": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "attach": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "unattach": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "silence": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "unsilence": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "unpage_user": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "bulk_action": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "preview_template": [RBACPermission.Permissions.INTEGRATIONS_TEST],
        "escalation_snapshot": [RBACPermission.Permissions.ALERT_GROUPS_READ],
    }

    queryset = AlertGroup.objects.none()  # needed for drf-spectacular introspection
    serializer_class = AlertGroupSerializer

    pagination_class = AlertGroupCursorPaginator

    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = (
        ["=public_primary_key", "=inside_organization_number", "web_title_cache"]
        if settings.FEATURE_ALERT_GROUP_SEARCH_ENABLED
        else []
    )
    filterset_class = AlertGroupFilter

    def get_serializer_class(self):
        if self.action == "list":
            return AlertGroupListSerializer

        return super().get_serializer_class()

    def get_queryset(self, ignore_filtering_by_available_teams=False):
        # no select_related or prefetch_related is used at this point, it will be done on paginate_queryset.

        alert_receive_channels_qs = AlertReceiveChannel.objects_with_deleted.filter(
            organization_id=self.request.auth.organization.id
        )
        if not ignore_filtering_by_available_teams:
            alert_receive_channels_qs = alert_receive_channels_qs.filter(*self.available_teams_lookup_args)

        # Filter by team(s). Since we really filter teams from integrations, this is not an AlertGroup model filter.
        # This is based on the common.api_helpers.ByTeamModelFieldFilterMixin implementation
        team_values = self.request.query_params.getlist("team", [])
        if team_values:
            null_team_lookup = Q(team__isnull=True) if NO_TEAM_VALUE in team_values else None
            teams_lookup = Q(team__public_primary_key__in=[ppk for ppk in team_values if ppk != NO_TEAM_VALUE])
            if null_team_lookup:
                teams_lookup = teams_lookup | null_team_lookup
            alert_receive_channels_qs = alert_receive_channels_qs.filter(teams_lookup)

        alert_receive_channels_ids = list(alert_receive_channels_qs.values_list("id", flat=True))
        queryset = AlertGroup.objects.filter(channel__in=alert_receive_channels_ids)

        # Filter by labels. Since alert group labels are "static" filter by names, not IDs.
        label_query = self.request.query_params.getlist("label", [])
        kv_pairs = parse_label_query(label_query)
        for key, value in kv_pairs:
            # Utilize (organization, key_name, value_name, alert_group) index on AlertGroupAssociatedLabel
            queryset = queryset.filter(
                labels__organization=self.request.auth.organization,
                labels__key_name=key,
                labels__value_name=value,
            )

        queryset = queryset.only("id")

        return queryset

    def paginate_queryset(self, queryset):
        """
        All SQL joins (select_related and prefetch_related) will be performed AFTER pagination, so it only joins tables
        for 25 alert groups, not the whole table.
        """
        alert_groups = super().paginate_queryset(queryset)
        alert_groups = self.enrich(alert_groups)
        return alert_groups

    def get_object(self):
        obj = super().get_object()
        obj = self.enrich([obj])[0]
        return obj

    def retrieve(self, request, *args, **kwargs):
        """Return alert group details.

        It is worth mentioning that `render_after_resolve_report_json` property will return a list
        of log entries including actions involving the alert group, notifications triggered for a user
        and resolution notes updates.

        A few additional notes about the possible values for each key in the logs:

        - `time`: humanized time delta respect to now when the action took place
        - `action`: human-readable description of the action
        - `realm`: resource involved in the action; one of three possible values:
        `alert_group`, `user_notification`, `resolution_note`
        - `type`: integer value indicating the type of action (see below)
        - `created_at`: timestamp corresponding to when the action happened
        - `author`: details about the user performing the action

        Possible `type` values depending on the realm value:

        For `alert_group`:
        - 0: Acknowledged
        - 1: Unacknowledged
        - 2: Invite
        - 3: Stop invitation
        - 4: Re-invite
        - 5: Escalation triggered
        - 6: Invitation triggered
        - 7: Silenced
        - 8: Attached
        - 9: Unattached
        - 10: Custom button triggered
        - 11: Unacknowledged by timeout
        - 12: Failed attachment
        - 13: Incident resolved
        - 14: Incident unresolved
        - 15: Unsilenced
        - 16: Escalation finished
        - 17: Escalation failed
        - 18: Acknowledge reminder triggered
        - 19: Wiped
        - 20: Deleted
        - 21: Incident registered
        - 22: A route is assigned to the incident
        - 23: Trigger direct paging escalation
        - 24: Unpage a user
        - 25: Restricted

        For `user_notification`:
        - 0: Personal notification triggered
        - 1: Personal notification finished
        - 2: Personal notification success,
        - 3: Personal notification failed

        For `resolution_note`:
        - 0: slack
        - 1: web

        """
        return super().retrieve(request, *args, **kwargs)

    def enrich(self, alert_groups: typing.List[AlertGroup]) -> typing.List[AlertGroup]:
        """
        This method performs select_related and prefetch_related (using setup_eager_loading) as well as in-memory joins
        to add additional info like alert_count and last_alert for every alert group efficiently.
        We need the last_alert because it's used by AlertGroupWebRenderer.
        """

        # enrich alert groups with select_related and prefetch_related
        alert_group_pks = [alert_group.pk for alert_group in alert_groups]
        queryset = AlertGroup.objects.filter(pk__in=alert_group_pks).order_by("-started_at")

        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        alert_groups = list(queryset)

        # get info on alerts count and last alert ID for every alert group
        alerts_info = (
            Alert.objects.values("group_id")
            .filter(group_id__in=alert_group_pks)
            .annotate(alerts_count=Count("group_id"), last_alert_id=Max("id"))
        )
        alerts_info_map = {info["group_id"]: info for info in alerts_info}

        # fetch last alerts for every alert group
        last_alert_ids = [info["last_alert_id"] for info in alerts_info_map.values()]
        last_alerts = Alert.objects.filter(pk__in=last_alert_ids)
        for alert in last_alerts:
            # link group back to alert
            alert.group = [alert_group for alert_group in alert_groups if alert_group.pk == alert.group_id][0]
            alerts_info_map[alert.group_id].update({"last_alert": alert})

        # add additional "alerts_count" and "last_alert" fields to every alert group
        for alert_group in alert_groups:
            try:
                alert_group.last_alert = alerts_info_map[alert_group.pk]["last_alert"]
                alert_group.alerts_count = alerts_info_map[alert_group.pk]["alerts_count"]
            except KeyError:
                # alert group has no alerts
                alert_group.last_alert = None
                alert_group.alerts_count = 0

        return alert_groups

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        delete_alert_group.apply_async((instance.pk, request.user.pk))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        filters=True,  # filter alert groups before counting them
        responses=inline_serializer(name="AlertGroupStats", fields={"count": serializers.IntegerField()}),
    )
    @action(methods=["get"], detail=False)
    def stats(self, request):
        """
        Return number of alert groups capped at 100001
        """
        MAX_COUNT = 100001
        alert_groups = self.filter_queryset(self.get_queryset())[:MAX_COUNT]
        count = alert_groups.count()
        count = f"{MAX_COUNT-1}+" if count == MAX_COUNT else str(count)
        return Response({"count": count})

    @extend_schema(responses=AlertGroupSerializer)
    @action(methods=["post"], detail=True)
    def acknowledge(self, request, pk):
        """
        Acknowledge an alert group
        """
        alert_group = self.get_object()
        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't acknowledge maintenance alert group")
        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't acknowledge an attached alert group")
        alert_group.acknowledge_by_user_or_backsync(self.request.user, action_source=ActionSource.WEB)

        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @extend_schema(responses=AlertGroupSerializer)
    @action(methods=["post"], detail=True)
    def unacknowledge(self, request, pk):
        """
        Unacknowledge an alert group
        """
        alert_group = self.get_object()
        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't unacknowledge maintenance alert group")

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't unacknowledge an attached alert group")

        if not alert_group.acknowledged:
            raise BadRequest(detail="The alert group is not acknowledged")

        if alert_group.resolved:
            raise BadRequest(detail="Can't unacknowledge a resolved alert group")

        alert_group.un_acknowledge_by_user_or_backsync(self.request.user, action_source=ActionSource.WEB)

        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @extend_schema(
        request=inline_serializer(
            name="AlertGroupResolve", fields={"resolution_note": serializers.CharField(required=False, allow_null=True)}
        ),
        responses=AlertGroupSerializer,
    )
    @action(methods=["post"], detail=True)
    def resolve(self, request, pk):
        """
        Resolve an alert group
        """
        alert_group = self.get_object()
        organization = self.request.user.organization

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't resolve an attached alert group")

        if alert_group.is_maintenance_incident:
            alert_group.stop_maintenance(self.request.user)
        else:
            resolution_note_text = request.data.get("resolution_note")
            if resolution_note_text:
                rn = ResolutionNote.objects.create(
                    alert_group=alert_group,
                    author=self.request.user,
                    source=(
                        ResolutionNote.Source.MOBILE_APP
                        if isinstance(self.request.successful_authenticator, MobileAppAuthTokenAuthentication)
                        else ResolutionNote.Source.WEB
                    ),
                    message_text=resolution_note_text[:3000],  # trim text to fit in the db field
                )
                send_update_resolution_note_signal.apply_async(
                    kwargs={
                        "alert_group_pk": alert_group.pk,
                        "resolution_note_pk": rn.pk,
                    }
                )
            else:
                # Check resolution note required setting only if resolution_note_text was not provided.
                if organization.is_resolution_note_required and not alert_group.has_resolution_notes:
                    return Response(
                        data={
                            "code": AlertGroupAPIError.RESOLUTION_NOTE_REQUIRED.value,
                            "detail": "Alert group without resolution note cannot be resolved due to organization settings",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            alert_group.resolve_by_user_or_backsync(self.request.user, action_source=ActionSource.WEB)
        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @extend_schema(responses=AlertGroupSerializer)
    @action(methods=["post"], detail=True)
    def unresolve(self, request, pk):
        """
        Unresolve an alert group
        """
        alert_group = self.get_object()
        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't unresolve maintenance alert group")

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't unresolve an attached alert group")

        if not alert_group.resolved:
            raise BadRequest(detail="The alert group is not resolved")

        alert_group.un_resolve_by_user_or_backsync(self.request.user, action_source=ActionSource.WEB)
        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @extend_schema(
        request=inline_serializer(name="AlertGroupAttach", fields={"root_alert_group_pk": serializers.CharField()}),
        responses=AlertGroupSerializer,
    )
    @action(methods=["post"], detail=True)
    def attach(self, request, pk=None):
        """
        Attach alert group to another alert group
        """
        alert_group = self.get_object()
        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't attach maintenance alert group")
        if alert_group.dependent_alert_groups.count() > 0:
            raise BadRequest(detail="Can't attach an alert group because it has another alert groups attached to it")
        if not alert_group.is_root_alert_group:
            raise BadRequest(detail="Can't attach an alert group because it has already been attached")

        try:
            root_alert_group = self.get_queryset().get(public_primary_key=request.data["root_alert_group_pk"])
        except AlertGroup.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if root_alert_group.resolved or root_alert_group.root_alert_group is not None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if root_alert_group == alert_group:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        alert_group.attach_by_user(self.request.user, root_alert_group, action_source=ActionSource.WEB)
        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @extend_schema(responses=AlertGroupSerializer)
    @action(methods=["post"], detail=True)
    def unattach(self, request, pk=None):
        """
        Unattach an alert group that is already attached to another alert group
        """
        alert_group = self.get_object()
        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't unattach maintenance alert group")
        if alert_group.is_root_alert_group:
            raise BadRequest(detail="Can't unattach an alert group because it is not attached")

        alert_group.un_attach_by_user(self.request.user, action_source=ActionSource.WEB)
        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @extend_schema(
        request=inline_serializer(name="AlertGroupSilence", fields={"delay": serializers.IntegerField()}),
        responses=AlertGroupSerializer,
    )
    @action(methods=["post"], detail=True)
    def silence(self, request, pk=None):
        """
        Silence an alert group for a specified delay
        """
        alert_group = self.get_object()

        delay = request.data.get("delay")
        if delay is None:
            raise BadRequest(detail="Please specify a delay for silence")

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't silence an attached alert group")

        alert_group.silence_by_user_or_backsync(request.user, silence_delay=delay, action_source=ActionSource.WEB)
        return Response(AlertGroupSerializer(alert_group, context={"request": request}).data)

    @extend_schema(
        responses=inline_serializer(
            name="AlertGroupSilenceOptions",
            fields={
                "value": serializers.ChoiceField(choices=[value for value, _ in AlertGroup.SILENCE_DELAY_OPTIONS]),
                "display_name": serializers.ChoiceField(
                    choices=[display_name for _, display_name in AlertGroup.SILENCE_DELAY_OPTIONS]
                ),
            },
            many=True,
        )
    )
    @action(methods=["get"], detail=False)
    def silence_options(self, request):
        # TODO: DEPRECATED, REMOVE IN A FUTURE RELEASE

        """
        Retrieve a list of valid silence options
        """
        data = [
            {"value": value, "display_name": display_name} for value, display_name in AlertGroup.SILENCE_DELAY_OPTIONS
        ]
        return Response(data)

    @extend_schema(responses=AlertGroupSerializer)
    @action(methods=["post"], detail=True)
    def unsilence(self, request, pk=None):
        """
        Unsilence a silenced alert group
        """
        alert_group = self.get_object()

        if not alert_group.silenced:
            raise BadRequest(detail="The alert group is not silenced")

        if alert_group.resolved:
            raise BadRequest(detail="Can't unsilence a resolved alert group")

        if alert_group.acknowledged:
            raise BadRequest(detail="Can't unsilence an acknowledged alert group")

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't unsilence an attached alert group")

        alert_group.un_silence_by_user_or_backsync(request.user, action_source=ActionSource.WEB)

        return Response(AlertGroupSerializer(alert_group, context={"request": request}).data)

    @extend_schema(
        request=inline_serializer(name="AlertGroupUnpageUser", fields={"user_id": serializers.CharField()}),
        responses=AlertGroupSerializer,
    )
    @action(methods=["post"], detail=True)
    def unpage_user(self, request, pk=None):
        """
        Remove a user that was directly paged for the alert group
        """
        organization = request.auth.organization
        from_user = request.user
        alert_group = self.get_object()

        try:
            user_id = request.data["user_id"]
        except KeyError:
            raise BadRequest(detail="Please specify user_id")

        try:
            user = organization.users.get(public_primary_key=user_id)
        except User.DoesNotExist:
            raise BadRequest(detail="User not found")

        unpage_user(alert_group=alert_group, user=user, from_user=from_user)
        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        responses=inline_serializer(
            name="AlertGroupFilters",
            fields={
                "name": serializers.CharField(),
                "type": serializers.CharField(),
                "href": serializers.CharField(required=False),
                "global": serializers.BooleanField(required=False),
                "default": serializers.JSONField(required=False),
                "description": serializers.CharField(required=False),
                "options": inline_serializer(
                    name="AlertGroupFiltersOptions",
                    fields={
                        "value": serializers.CharField(),
                        "display_name": serializers.IntegerField(),
                    },
                ),
            },
            many=True,
        )
    )
    @action(methods=["get"], detail=False)
    def filters(self, request):
        """
        Retrieve a list of valid filter options that can be used to filter alert groups
        """
        api_root = "/api/internal/v1/"
        default_day_range = 30

        default_datetime_range = f"now-{default_day_range}d_now"

        filter_options = [
            {
                "name": "team",
                "type": "team_select",
                "href": api_root + "teams/",
                "global": True,
            },
            {"name": "search", "type": "search"},
            {"name": "integration", "type": "options", "href": api_root + "alert_receive_channels/?filters=true"},
            {"name": "escalation_chain", "type": "options", "href": api_root + "escalation_chains/?filters=true"},
            {
                "name": "acknowledged_by",
                "type": "options",
                "href": api_root + "users/?filters=true&roles=0&roles=1&roles=2",
                "default": {"display_name": self.request.user.username, "value": self.request.user.public_primary_key},
            },
            {
                "name": "resolved_by",
                "type": "options",
                "href": api_root + "users/?filters=true&roles=0&roles=1&roles=2",
            },
            {
                "name": "silenced_by",
                "type": "options",
                "href": api_root + "users/?filters=true&roles=0&roles=1&roles=2",
            },
            {
                "name": "invitees_are",
                "type": "options",
                "href": api_root + "users/?filters=true&roles=0&roles=1&roles=2",
            },
            {
                "name": "involved_users_are",
                "type": "options",
                "href": api_root + "users/?filters=true&roles=0&roles=1&roles=2",
                "default": {"display_name": self.request.user.username, "value": self.request.user.public_primary_key},
                "description": f"This filter works only for last {AlertGroupFilter.FILTER_BY_INVOLVED_USERS_ALERT_GROUPS_CUTOFF} alert groups these users involved in.",
            },
            {
                "name": "status",
                "type": "options",
                "options": [
                    {"display_name": "firing", "value": AlertGroup.NEW},
                    {"display_name": "acknowledged", "value": AlertGroup.ACKNOWLEDGED},
                    {"display_name": "resolved", "value": AlertGroup.RESOLVED},
                    {"display_name": "silenced", "value": AlertGroup.SILENCED},
                ],
            },
            {
                "name": "started_at",
                "type": "daterange",
                "default": default_datetime_range,
            },
            {
                "name": "resolved_at",
                "type": "daterange",
                "default": default_datetime_range,
            },
            {
                "name": "with_resolution_note",
                "type": "boolean",
                "default": "true",
            },
            {
                "name": "mine",
                "type": "boolean",
                "default": "true",
                "description": f"This filter works only for last {AlertGroupFilter.FILTER_BY_INVOLVED_USERS_ALERT_GROUPS_CUTOFF} alert groups you're involved in.",
            },
        ]

        if is_labels_feature_enabled(self.request.auth.organization):
            filter_options.append(
                {
                    "name": "label",
                    "display_name": "Label",
                    "type": "alert_group_labels",
                }
            )

        return Response(filter_options)

    @extend_schema(
        request=inline_serializer(
            name="AlertGroupBulkActionRequest",
            fields={
                "alert_group_pks": serializers.ListField(child=serializers.CharField()),
                "action": serializers.ChoiceField(choices=AlertGroup.BULK_ACTIONS),
                "delay": serializers.IntegerField(
                    required=False, allow_null=True, help_text="only applicable for silence"
                ),
            },
        )
    )
    @action(methods=["post"], detail=False)
    def bulk_action(self, request):
        """
        Perform a bulk action on a list of alert groups
        """
        alert_group_pks = self.request.data.get("alert_group_pks", [])
        action_name = self.request.data.get("action", None)
        delay = self.request.data.get("delay")
        kwargs = {}

        if action_name not in AlertGroup.BULK_ACTIONS:
            return Response("Unknown action", status=status.HTTP_400_BAD_REQUEST)

        if action_name == AlertGroup.SILENCE:
            if delay is None:
                raise BadRequest(detail="Please specify a delay for silence")
            kwargs["silence_delay"] = delay

        alert_groups = AlertGroup.objects.filter(
            channel__organization=self.request.auth.organization, public_primary_key__in=alert_group_pks
        )

        kwargs["user"] = self.request.user
        kwargs["alert_groups"] = alert_groups

        method = getattr(AlertGroup, f"bulk_{action_name}")
        method(**kwargs)

        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        responses=inline_serializer(
            name="AlertGroupBulkActionOptions",
            fields={
                "value": serializers.ChoiceField(choices=AlertGroup.BULK_ACTIONS),
                "display_name": serializers.ChoiceField(choices=AlertGroup.BULK_ACTIONS),
            },
            many=True,
        )
    )
    @action(methods=["get"], detail=False)
    def bulk_action_options(self, request):
        """
        Retrieve a list of valid bulk action options
        """
        return Response(
            [{"value": action_name, "display_name": action_name} for action_name in AlertGroup.BULK_ACTIONS]
        )

    # This method is required for PreviewTemplateMixin
    def get_alert_to_template(self, payload=None):
        return self.get_object().alerts.first()

    @action(methods=["get"], detail=True)
    def escalation_snapshot(self, request, pk=None):
        alert_group = self.get_object()
        escalation_snapshot = alert_group.escalation_snapshot
        result = AlertGroupEscalationSnapshotAPISerializer(escalation_snapshot).data if escalation_snapshot else {}
        return Response(result)
