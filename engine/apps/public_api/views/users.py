from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.auth_token.auth import ApiTokenAuthentication, UserScheduleExportAuthentication
from apps.public_api.custom_renderers import CalendarRenderer
from apps.public_api.serializers import FastUserSerializer, UserSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.schedules.ical_utils import user_ical_export
from apps.schedules.models import OnCallSchedule
from apps.user_management.models import User
from common.api_helpers.mixins import RateLimitHeadersMixin, ShortSerializerMixin
from common.api_helpers.paginators import HundredPageSizePaginator


class UserView(RateLimitHeadersMixin, ShortSerializerMixin, ReadOnlyModelViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    model = User
    pagination_class = HundredPageSizePaginator

    serializer_class = UserSerializer
    short_serializer_class = FastUserSerializer

    throttle_classes = [UserThrottle]

    def get_queryset(self):
        username = self.request.query_params.get("username")
        email = self.request.query_params.get("email")
        is_short_request = self.request.query_params.get("short", "false") == "true"
        queryset = self.request.auth.organization.users.all()

        if username is not None:
            queryset = queryset.filter(username=username)

        if email is not None:
            queryset = queryset.filter(email=email)

        if not is_short_request:
            queryset = self.serializer_class.setup_eager_loading(queryset)
        return queryset.order_by("id")

    def get_object(self):
        public_primary_key = self.kwargs["pk"]

        if public_primary_key == "current":
            return self.request.user

        organization = self.request.auth.organization

        try:
            user = User.objects.get(public_primary_key=public_primary_key, organization=organization)
        except User.DoesNotExist:
            raise NotFound

        return user

    @action(
        methods=["get"],
        detail=True,
        renderer_classes=(CalendarRenderer,),
        authentication_classes=(UserScheduleExportAuthentication,),
        permission_classes=(IsAuthenticated,),
    )
    def schedule_export(self, request, pk):
        schedules = OnCallSchedule.objects.filter(organization=self.request.auth.organization)
        export = user_ical_export(self.request.user, schedules)
        return Response(export)
