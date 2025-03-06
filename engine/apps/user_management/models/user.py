import datetime
import logging
import re
import typing
from urllib.parse import urljoin

import pytz
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from emoji import demojize

from apps.api.permissions import (
    GrafanaAPIPermissions,
    LegacyAccessControlCompatiblePermission,
    LegacyAccessControlRole,
    RBACPermission,
    convert_oncall_permission_to_irm,
    user_is_authorized,
)
from apps.google import utils as google_utils
from apps.google.models import GoogleOAuth2User
from apps.schedules.tasks import drop_cached_ical_for_custom_events_for_organization
from apps.user_management.types import AlertGroupTableColumn, GoogleCalendarSettings
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import AlertGroup, EscalationPolicy
    from apps.auth_token.models import ApiAuthToken, ScheduleExportAuthToken, UserScheduleExportAuthToken
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
    from apps.slack.models import SlackUserIdentity
    from apps.social_auth.types import GoogleOauth2Response
    from apps.user_management.models import Organization, Team

logger = logging.getLogger(__name__)


def generate_public_primary_key_for_user():
    prefix = "U"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while User.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="User"
        )
        failure_counter += 1

    return new_public_primary_key


def default_working_hours():
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    weekends = ["saturday", "sunday"]

    working_hours = {day: [{"start": "09:00:00", "end": "17:00:00"}] for day in weekdays}
    working_hours |= {day: [] for day in weekends}

    return working_hours


class UserManager(models.Manager["User"]):
    pass


class UserQuerySet(models.QuerySet):
    def filter(self, *args, **kwargs):
        return super().filter(*args, **kwargs, is_active=True)

    def filter_with_deleted(self, *args, **kwargs):
        return super().filter(*args, **kwargs)

    def filter_by_permission(
        self, permission: LegacyAccessControlCompatiblePermission, organization: "Organization", *args, **kwargs
    ):
        """
        This method builds a filter query that is compatible with RBAC as well as legacy "basic" role based
        authorization. If a permission is provided we simply do a regex search where the permission column
        contains the permission value (need to use regex because the JSON contains method is not supported by sqlite).

        Additionally, if `organization.is_grafana_irm_enabled` is True, we convert the permission to the IRM version
        when filtering.

        Lastly, if RBAC is not supported for the org, we make the assumption that we are looking for any users with AT
        LEAST the fallback role. Ex: if the fallback role were editor than we would get editors and admins.
        """
        if organization.is_rbac_permissions_enabled:
            permission_value = (
                convert_oncall_permission_to_irm(permission)
                if organization.is_grafana_irm_enabled
                else permission.value
            )

            # https://stackoverflow.com/a/50251879
            if settings.DATABASE_TYPE == settings.DATABASE_TYPES.SQLITE3:
                # contains is not supported on sqlite
                # https://docs.djangoproject.com/en/4.2/topics/db/queries/#contains
                query = Q(permissions__regex=re.escape(permission_value))
            else:
                query = Q(permissions__contains=GrafanaAPIPermissions.construct_permissions([permission_value]))
        else:
            query = Q(role__lte=permission.fallback_role.value)

        return self.filter(
            query,
            *args,
            **kwargs,
            organization=organization,
        )

    def delete(self):
        # is_active = None is used to be able to have multiple deleted users with the same user_id
        return super().update(is_active=None)

    def hard_delete(self):
        return super().delete()


class User(models.Model):
    acknowledged_alert_groups: "RelatedManager['AlertGroup']"
    auth_tokens: "RelatedManager['ApiAuthToken']"
    current_team: typing.Optional["Team"]
    escalation_policy_notify_queues: "RelatedManager['EscalationPolicy']"
    google_oauth2_user: typing.Optional[GoogleOAuth2User]
    last_notified_in_escalation_policies: "RelatedManager['EscalationPolicy']"
    notification_policies: "RelatedManager['UserNotificationPolicy']"
    organization: "Organization"
    personal_log_records: "RelatedManager['UserNotificationPolicyLogRecord']"
    resolved_alert_groups: "RelatedManager['AlertGroup']"
    schedule_export_token: "RelatedManager['ScheduleExportAuthToken']"
    silenced_alert_groups: "RelatedManager['AlertGroup']"
    slack_user_identity: typing.Optional["SlackUserIdentity"]
    teams: "RelatedManager['Team']"
    user_schedule_export_token: "RelatedManager['UserScheduleExportAuthToken']"
    wiped_alert_groups: "RelatedManager['AlertGroup']"

    # mypy/django-stubs support isn't 100% there for this.. however, manually typing this (to what it actually is)
    # works for now. See this issue for more details
    # https://github.com/typeddjango/django-stubs/issues/353#issuecomment-1095656633
    objects: UserQuerySet = UserManager.from_queryset(UserQuerySet)()

    class Meta:
        # For some reason there are cases when Grafana user gets deleted,
        # and then new Grafana user is created with the same user_id
        # Including is_active to unique_together and setting is_active to None allows to
        # have multiple deleted users with the same user_id, but user_id is unique among active users
        unique_together = ("user_id", "organization", "is_active")
        indexes = [
            models.Index(fields=["is_active", "organization", "username"]),
            models.Index(fields=["is_active", "organization", "email"]),
        ]

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_user,
    )

    user_id = models.PositiveIntegerField()
    organization = models.ForeignKey(to="user_management.Organization", on_delete=models.CASCADE, related_name="users")
    current_team = models.ForeignKey(
        to="user_management.Team", null=True, default=None, on_delete=models.SET_NULL, related_name="current_team_users"
    )

    email = models.EmailField()
    name = models.CharField(max_length=300)
    username = models.CharField(max_length=300)
    role = models.PositiveSmallIntegerField(choices=LegacyAccessControlRole.choices())
    avatar_url = models.URLField()

    # don't use "_timezone" directly, use the "timezone" property since it can be populated via slack user identity
    _timezone = models.CharField(max_length=50, null=True, default=None)
    working_hours = models.JSONField(null=True, default=default_working_hours)

    notification = models.ManyToManyField(
        "alerts.AlertGroup", through="alerts.UserHasNotification", related_name="users"
    )

    unverified_phone_number = models.CharField(max_length=20, null=True, default=None)
    _verified_phone_number = models.CharField(max_length=20, null=True, default=None)
    hide_phone_number = models.BooleanField(default=False)

    slack_user_identity = models.ForeignKey(
        "slack.SlackUserIdentity", on_delete=models.PROTECT, null=True, default=None, related_name="users"
    )

    # is_active = None is used to be able to have multiple deleted users with the same user_id
    is_active = models.BooleanField(null=True, default=True)
    permissions = models.JSONField(null=False, default=list)

    alert_group_table_selected_columns: list[AlertGroupTableColumn] | None = models.JSONField(default=None, null=True)

    google_calendar_settings: GoogleCalendarSettings | None = models.JSONField(default=None, null=True)

    def __str__(self):
        return f"{self.pk}: {self.username}"

    @property
    def is_admin(self) -> bool:
        return user_is_authorized(self, [RBACPermission.Permissions.ADMIN])

    @property
    def available_teams(self) -> "RelatedManager['Team']":
        if self.is_admin:
            return self.organization.teams.all()
        return self.organization.teams.filter(Q(is_sharing_resources_to_all=True) | Q(users=self)).distinct()

    @property
    def is_notification_allowed(self) -> bool:
        return user_is_authorized(self, [RBACPermission.Permissions.NOTIFICATIONS_READ])

    @property
    def is_authenticated(self):
        return True

    @property
    def is_service_account(self) -> bool:
        return False

    @property
    def has_google_oauth2_connected(self) -> bool:
        try:
            # https://stackoverflow.com/a/35005034/3902555
            return self.google_oauth2_user is not None
        except ObjectDoesNotExist:
            return False

    @property
    def google_oauth2_token_is_missing_scopes(self) -> bool:
        if not self.has_google_oauth2_connected:
            return False
        return not google_utils.user_granted_all_required_scopes(self.google_oauth2_user.oauth_scope)

    def avatar_full_url(self, organization: "Organization"):
        """
        Use arg `organization` instead of `self.organization` to avoid multiple requests to db when getting avatar for
        users list
        """
        return urljoin(organization.grafana_url, self.avatar_url)

    @property
    def verified_phone_number(self) -> str | None:
        """
        Use property to highlight that _verified_phone_number should not be modified directly
        """
        return self._verified_phone_number

    def save_verified_phone_number(self, phone_number: str) -> None:
        self._verified_phone_number = phone_number
        self.save(update_fields=["_verified_phone_number"])

    def clear_phone_numbers(self) -> None:
        self.unverified_phone_number = None
        self._verified_phone_number = None
        self.save(update_fields=["unverified_phone_number", "_verified_phone_number"])

    # TODO: move to telegram app
    @property
    def is_telegram_connected(self):
        return hasattr(self, "telegram_connection")

    def self_or_has_user_settings_admin_permission(self, user_to_check: "User", organization: "Organization") -> bool:
        has_permission = user_is_authorized(user_to_check, [RBACPermission.Permissions.USER_SETTINGS_ADMIN])
        return user_to_check.pk == self.pk or (has_permission and organization.pk == user_to_check.organization_id)

    def get_username_with_slack_verbal(self, mention=False) -> str:
        slack_verbal = None

        if self.slack_user_identity:
            slack_verbal = (
                f"<@{self.slack_user_identity.slack_id}>"
                if mention
                else f"@{self.slack_user_identity.profile_display_name or self.slack_user_identity.slack_verbal}"
            )

        if slack_verbal:
            return f"{self.username} ({slack_verbal})"

        return self.username

    @property
    def timezone(self) -> typing.Optional[str]:
        if self._timezone:
            return self._timezone

        if self.slack_user_identity:
            return self.slack_user_identity.timezone

        return None

    @timezone.setter
    def timezone(self, value):
        self._timezone = value

    def is_in_working_hours(self, dt: datetime.datetime, tz: typing.Optional[str] = None) -> bool:
        assert dt.tzinfo == datetime.timezone.utc, "dt must be in UTC"

        # Default to user's timezone
        if not tz:
            tz = self.timezone

        # If user has no timezone set, any time is considered non-working hours
        if not tz:
            return False

        # Convert to user's timezone and get day name (e.g. monday)
        dt = dt.astimezone(pytz.timezone(tz))
        day_name = dt.date().strftime("%A").lower()

        # If no working hours for the day, return False
        if day_name not in self.working_hours or not self.working_hours[day_name]:
            return False

        # Extract start and end time for the day from working hours
        day_start_time_str = self.working_hours[day_name][0]["start"]
        day_start_time = datetime.time.fromisoformat(day_start_time_str)

        day_end_time_str = self.working_hours[day_name][0]["end"]
        day_end_time = datetime.time.fromisoformat(day_end_time_str)

        # Calculate day start and end datetime
        day_start = dt.replace(
            hour=day_start_time.hour, minute=day_start_time.minute, second=day_start_time.second, microsecond=0
        )
        day_end = dt.replace(
            hour=day_end_time.hour, minute=day_end_time.minute, second=day_end_time.second, microsecond=0
        )

        return day_start <= dt <= day_end

    def short(self, organization):
        return {
            "username": self.username,
            "pk": self.public_primary_key,
            "avatar": self.avatar_url,
            "avatar_full": self.avatar_full_url(organization),
        }

    # Insight logs
    @property
    def insight_logs_type_verbal(self):
        return "user"

    @property
    def insight_logs_verbal(self):
        return self.username

    @property
    def insight_logs_serialized(self):
        from apps.base.models import UserNotificationPolicy

        default, important = UserNotificationPolicy.get_short_verbals_for_user(user=self)
        notification_policies_verbal = f"default: {' - '.join(default)}, important: {' - '.join(important)}"
        notification_policies_verbal = demojize(notification_policies_verbal)

        result = {
            "username": self.username,
            # LEGACY.. role should get removed eventually.. it's probably safe to remove it now?
            "role": self.get_role_display(),
            "notification_policies": notification_policies_verbal,
        }
        if self.verified_phone_number:
            result["verified_phone_number"] = self.unverified_phone_number
        if self.unverified_phone_number:
            result["unverified_phone_number"] = self.unverified_phone_number
        return result

    @property
    def insight_logs_metadata(self):
        return {}

    def get_default_fallback_notification_policy(self) -> "UserNotificationPolicy":
        from apps.base.models import UserNotificationPolicy

        return UserNotificationPolicy.get_default_fallback_policy(self)

    def get_notification_policies_or_use_default_fallback(
        self, important=False
    ) -> typing.Tuple[bool, typing.List["UserNotificationPolicy"]]:
        """
        If the user has no notification policies defined, fallback to using e-mail as the notification channel.

        The 1st tuple element is a boolean indicating if we are falling back to using a "fallback"/default
        notification policy step (which occurs when the user has no notification policies defined).
        """
        notification_polices = self.notification_policies.filter(important=important)

        if not notification_polices.exists():
            return (
                True,
                [self.get_default_fallback_notification_policy()],
            )
        return (
            False,
            list(notification_polices.all()),
        )

    def update_alert_group_table_selected_columns(self, columns: typing.List[AlertGroupTableColumn]) -> None:
        if self.alert_group_table_selected_columns != columns:
            self.alert_group_table_selected_columns = columns
            self.save(update_fields=["alert_group_table_selected_columns"])

    def save_google_oauth2_settings(self, google_oauth2_response: "GoogleOauth2Response") -> None:
        logger.info(
            f"Saving Google OAuth2 settings for user {self.pk} "
            f"sub={google_oauth2_response.get('sub')} "
            f"oauth_scope={google_oauth2_response.get('scope')}"
        )

        _, created = GoogleOAuth2User.objects.update_or_create(
            user=self,
            defaults={
                "google_user_id": google_oauth2_response.get("sub"),
                "access_token": google_oauth2_response.get("access_token"),
                "refresh_token": google_oauth2_response.get("refresh_token"),
                "oauth_scope": google_oauth2_response.get("scope"),
            },
        )
        if created:
            self.google_calendar_settings = {
                "oncall_schedules_to_consider_for_shift_swaps": [],
            }
            self.save(update_fields=["google_calendar_settings"])

    def reset_google_oauth2_settings(self) -> None:
        logger.info(f"Resetting Google OAuth2 settings for user {self.pk}")

        GoogleOAuth2User.objects.filter(user=self).delete()

        self.google_calendar_settings = None
        self.save(update_fields=["google_calendar_settings"])


# TODO: check whether this signal can be moved to save method of the model
@receiver(post_save, sender=User)
def listen_for_user_model_save(sender: User, instance: User, created: bool, *args, **kwargs) -> None:
    drop_cached_ical_for_custom_events_for_organization.apply_async(
        (instance.organization_id,),
    )
