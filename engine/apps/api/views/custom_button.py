from django.core.exceptions import ObjectDoesNotExist
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import CustomButton
from apps.api.permissions import RBACPermission
from apps.api.serializers.custom_button import CustomButtonSerializer
from apps.auth_token.auth import PluginAuthentication
from common.api_helpers.filters import ByTeamModelFieldFilterMixin, ModelFieldFilterMixin, TeamModelMultipleChoiceFilter
from common.api_helpers.mixins import PublicPrimaryKeyMixin, TeamFilteringMixin
from common.insight_log import EntityEvent, write_resource_insight_log


class CustomButtonFilter(ByTeamModelFieldFilterMixin, ModelFieldFilterMixin, filters.FilterSet):
    team = TeamModelMultipleChoiceFilter()


class CustomButtonView(TeamFilteringMixin, PublicPrimaryKeyMixin, ModelViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "metadata": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_READ],
        "filters": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_READ],
        "list": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_READ],
        "retrieve": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_READ],
        "create": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_WRITE],
        "update": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_WRITE],
        "partial_update": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_WRITE],
        "destroy": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_WRITE],
    }

    model = CustomButton
    serializer_class = CustomButtonSerializer

    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ["public_primary_key", "name"]
    filterset_class = CustomButtonFilter

    def get_queryset(self, ignore_filtering_by_available_teams=False):
        queryset = CustomButton.objects.filter(
            organization=self.request.auth.organization,
        )
        if not ignore_filtering_by_available_teams:
            queryset = queryset.filter(*self.available_teams_lookup_args).distinct()

        return queryset

    def get_object(self):
        # get the object from the whole organization if there is a flag `get_from_organization=true`
        # otherwise get the object from the current team
        get_from_organization = self.request.query_params.get("from_organization", "false") == "true"
        if get_from_organization:
            return self.get_object_from_organization()
        return super().get_object()

    def get_object_from_organization(self):
        # use this method to get the object from the whole organization instead of the current team
        pk = self.kwargs["pk"]
        organization = self.request.auth.organization
        try:
            obj = (
                organization.custom_buttons.filter(*self.available_teams_lookup_args)
                .distinct()
                .get(public_primary_key=pk)
            )
        except ObjectDoesNotExist:
            raise NotFound

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def perform_create(self, serializer):
        serializer.save()
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.CREATED,
        )

    def perform_update(self, serializer):
        prev_state = serializer.instance.insight_logs_serialized
        serializer.save()
        new_state = serializer.instance.insight_logs_serialized
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )

    def perform_destroy(self, instance):
        write_resource_insight_log(
            instance=instance,
            author=self.request.user,
            event=EntityEvent.DELETED,
        )
        instance.delete()

    @action(methods=["get"], detail=False)
    def filters(self, request):
        filter_name = request.query_params.get("search", None)
        api_root = "/api/internal/v1/"

        filter_options = [
            {
                "name": "team",
                "type": "team_select",
                "href": api_root + "teams/",
                "global": True,
            },
        ]

        if filter_name is not None:
            filter_options = list(filter(lambda f: filter_name in f["name"], filter_options))

        return Response(filter_options)
