from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Max
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.alerts.constants import ActionSource
from apps.alerts.models import Alert, AlertGroup, AlertReceiveChannel, ResolutionNote
from apps.alerts.paging import unpage_user
from apps.alerts.tasks import send_update_resolution_note_signal
from apps.api.errors import AlertGroupAPIError
from apps.api.permissions import RBACPermission
from apps.api.serializers.v1.alert_group import AlertGroupListSerializer, AlertGroupSerializer
from apps.api.serializers.v1.team import TeamSerializer
from apps.api.views.common.alert_group import STATS_MAX_COUNT, AlertGroupFilter, AlertGroupFilterBackend
from apps.auth_token.auth import PluginAuthentication
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
from apps.user_management.models import Team, User
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.filters import DateRangeFilterMixin
from common.api_helpers.mixins import PreviewTemplateMixin, PublicPrimaryKeyMixin, TeamFilteringMixin
from common.api_helpers.paginators import TwentyFiveCursorPaginator


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
            queryset = AlertGroup.unarchived_objects.filter(
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
    PublicPrimaryKeyMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
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
        "create": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
        "update": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
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
    }

    http_method_names = ["get", "post"]

    serializer_class = AlertGroupSerializer

    pagination_class = TwentyFiveCursorPaginator

    filter_backends = [SearchFilter, AlertGroupFilterBackend]
    # search_fields = ["=public_primary_key", "=inside_organization_number", "web_title_cache"]

    filterset_class = AlertGroupFilter

    def get_serializer_class(self):
        if self.action == "list":
            return AlertGroupListSerializer

        return super().get_serializer_class()

    def get_queryset(self, ignore_filtering_by_available_teams=False):
        # no select_related or prefetch_related is used at this point, it will be done on paginate_queryset.

        alert_receive_channels_qs = AlertReceiveChannel.objects.filter(
            organization_id=self.request.auth.organization.id
        )
        if not ignore_filtering_by_available_teams:
            alert_receive_channels_qs = alert_receive_channels_qs.filter(*self.available_teams_lookup_args)

        alert_receive_channels_ids = list(alert_receive_channels_qs.values_list("id", flat=True))

        queryset = AlertGroup.unarchived_objects.filter(
            channel__in=alert_receive_channels_ids,
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

    def enrich(self, alert_groups):
        """
        This method performs select_related and prefetch_related (using setup_eager_loading) as well as in-memory joins
        to add additional info like alert_count and last_alert for every alert group efficiently.
        We need the last_alert because it's used by AlertGroupWebRenderer.
        """

        # enrich alert groups with select_related and prefetch_related
        alert_group_pks = [alert_group.pk for alert_group in alert_groups]
        queryset = AlertGroup.all_objects.filter(pk__in=alert_group_pks).order_by("-pk")

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

    @action(detail=False)
    def stats(self, *args, **kwargs):
        alert_groups = self.filter_queryset(self.get_queryset())[:STATS_MAX_COUNT]
        count = alert_groups.count()
        count = f"{STATS_MAX_COUNT-1}+" if count == STATS_MAX_COUNT else str(count)
        return Response(
            {
                "count": count,
            }
        )

    @action(methods=["post"], detail=True)
    def acknowledge(self, request, pk):
        alert_group = self.get_object()
        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't acknowledge maintenance alert group")
        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't acknowledge an attached alert group")
        alert_group.acknowledge_by_user(self.request.user, action_source=ActionSource.WEB)

        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @action(methods=["post"], detail=True)
    def unacknowledge(self, request, pk):
        alert_group = self.get_object()
        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't unacknowledge maintenance alert group")

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't unacknowledge an attached alert group")

        if not alert_group.acknowledged:
            raise BadRequest(detail="The alert group is not acknowledged")

        if alert_group.resolved:
            raise BadRequest(detail="Can't unacknowledge a resolved alert group")

        alert_group.un_acknowledge_by_user(self.request.user, action_source=ActionSource.WEB)

        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @action(methods=["post"], detail=True)
    def resolve(self, request, pk):
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
                    source=ResolutionNote.Source.WEB,
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
            alert_group.resolve_by_user(self.request.user, action_source=ActionSource.WEB)
        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @action(methods=["post"], detail=True)
    def unresolve(self, request, pk):
        alert_group = self.get_object()
        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't unresolve maintenance alert group")

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't unresolve an attached alert group")

        if not alert_group.resolved:
            raise BadRequest(detail="The alert group is not resolved")

        alert_group.un_resolve_by_user(self.request.user, action_source=ActionSource.WEB)
        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @action(methods=["post"], detail=True)
    def attach(self, request, pk=None):
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

    @action(methods=["post"], detail=True)
    def unattach(self, request, pk=None):
        alert_group = self.get_object()
        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't unattach maintenance alert group")
        if alert_group.is_root_alert_group:
            raise BadRequest(detail="Can't unattach an alert group because it is not attached")

        alert_group.un_attach_by_user(self.request.user, action_source=ActionSource.WEB)
        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @action(methods=["post"], detail=True)
    def silence(self, request, pk=None):
        alert_group = self.get_object()

        delay = request.data.get("delay")
        if delay is None:
            raise BadRequest(detail="Please specify a delay for silence")

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't silence an attached alert group")

        alert_group.silence_by_user(request.user, silence_delay=delay, action_source=ActionSource.WEB)
        return Response(AlertGroupSerializer(alert_group, context={"request": request}).data)

    @action(methods=["get"], detail=False)
    def silence_options(self, request):
        data = [
            {"value": value, "display_name": display_name} for value, display_name in AlertGroup.SILENCE_DELAY_OPTIONS
        ]
        return Response(data)

    @action(methods=["post"], detail=True)
    def unsilence(self, request, pk=None):
        alert_group = self.get_object()

        if not alert_group.silenced:
            raise BadRequest(detail="The alert group is not silenced")

        if alert_group.resolved:
            raise BadRequest(detail="Can't unsilence a resolved alert group")

        if alert_group.acknowledged:
            raise BadRequest(detail="Can't unsilence an acknowledged alert group")

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't unsilence an attached alert group")

        alert_group.un_silence_by_user(request.user, action_source=ActionSource.WEB)

        return Response(AlertGroupSerializer(alert_group, context={"request": request}).data)

    @action(methods=["post"], detail=True)
    def unpage_user(self, request, pk=None):
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

    @action(methods=["get"], detail=False)
    def filters(self, request):
        filter_name = request.query_params.get("search", None)
        api_root = "/api/internal/v1/"

        now = timezone.now()
        week_ago = now - timedelta(days=7)

        default_datetime_range = "{}/{}".format(
            week_ago.strftime(DateRangeFilterMixin.DATE_FORMAT),
            now.strftime(DateRangeFilterMixin.DATE_FORMAT),
        )

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
            # {'name': 'is_root', 'type': 'boolean', 'default': True},
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

        if filter_name is not None:
            filter_options = list(filter(lambda f: filter_name in f["name"], filter_options))

        return Response(filter_options)

    @action(methods=["post"], detail=False)
    def bulk_action(self, request):
        alert_group_public_pks = self.request.data.get("alert_group_pks", [])
        action_with_incidents = self.request.data.get("action", None)
        delay = self.request.data.get("delay")
        kwargs = {}

        if action_with_incidents not in AlertGroup.BULK_ACTIONS:
            return Response("Unknown action", status=status.HTTP_400_BAD_REQUEST)

        if action_with_incidents == AlertGroup.SILENCE:
            if delay is None:
                raise BadRequest(detail="Please specify a delay for silence")
            kwargs["silence_delay"] = delay

        alert_groups = AlertGroup.unarchived_objects.filter(
            channel__organization=self.request.auth.organization, public_primary_key__in=alert_group_public_pks
        )

        kwargs["user"] = self.request.user
        kwargs["alert_groups"] = alert_groups

        method = getattr(AlertGroup, f"bulk_{action_with_incidents}")
        method(**kwargs)

        return Response(status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False)
    def bulk_action_options(self, request):
        return Response(
            [{"value": action_name, "display_name": action_name} for action_name in AlertGroup.BULK_ACTIONS]
        )

    # This method is required for PreviewTemplateMixin
    def get_alert_to_template(self, payload=None):
        return self.get_object().alerts.first()
