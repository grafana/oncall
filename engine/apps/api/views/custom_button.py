from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import AlertGroup, CustomButton
from apps.alerts.tasks.custom_button_result import custom_button_result
from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin, IsAdminOrEditor
from apps.api.serializers.custom_button import CustomButtonSerializer
from apps.auth_token.auth import PluginAuthentication
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.insight_log import EntityEvent, write_resource_insight_log


class CustomButtonView(PublicPrimaryKeyMixin, ModelViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)
    action_permissions = {
        IsAdmin: MODIFY_ACTIONS,
        IsAdminOrEditor: ("action",),
        AnyRole: READ_ACTIONS,
    }

    model = CustomButton
    serializer_class = CustomButtonSerializer

    def get_queryset(self):
        queryset = CustomButton.objects.filter(
            organization=self.request.auth.organization,
            team=self.request.user.current_team,
        )
        return queryset

    def get_object(self):
        # Override this method because we want to get object from organization instead of concrete team.
        pk = self.kwargs["pk"]
        organization = self.request.auth.organization

        try:
            obj = organization.custom_buttons.get(public_primary_key=pk)
        except ObjectDoesNotExist:
            raise NotFound

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def original_get_object(self):
        return super().get_object()

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

    @action(detail=True, methods=["post"])
    def action(self, request, pk):
        alert_group_id = request.query_params.get("alert_group", None)
        if alert_group_id is not None:
            custom_button = self.original_get_object()
            try:
                alert_group = AlertGroup.unarchived_objects.get(
                    public_primary_key=alert_group_id, channel=custom_button.alert_receive_channel
                )
                custom_button_result.apply_async((custom_button.pk, alert_group.pk, self.request.user.pk))
            except AlertGroup.DoesNotExist:
                raise BadRequest(detail="AlertGroup does not exist or archived")
            return Response(status=status.HTTP_200_OK)
        else:
            raise BadRequest(detail="AlertGroup is required")
