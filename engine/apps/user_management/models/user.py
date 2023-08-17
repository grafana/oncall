import datetime
import json
import logging
import typing
from urllib.parse import urljoin

import pytz
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from emoji import demojize

from apps.api.permissions import (
    LegacyAccessControlCompatiblePermission,
    LegacyAccessControlRole,
    RBACPermission,
    user_is_authorized,
)
from apps.schedules.tasks import drop_cached_ical_for_custom_events_for_organization
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import AlertGroup, EscalationPolicy
    from apps.auth_token.models import ApiAuthToken, ScheduleExportAuthToken, UserScheduleExportAuthToken
    from apps.base.models import UserNotificationPolicy
    from apps.slack.models import SlackUserIdentity
    from apps.user_management.models import Organization, Team

logger = logging.getLogger(__name__)


class PermissionsRegexQuery(typing.TypedDict):
    permissions__regex: str


class RoleInQuery(typing.TypedDict):
    role__in: typing.List[int]


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
    @staticmethod
    def sync_for_team(team, api_members: list[dict]):
        user_ids = tuple(member["userId"] for member in api_members)
        users = team.organization.users.filter(user_id__in=user_ids)
        team.users.set(users)

    @staticmethod
    def sync_for_organization(organization, api_users: list[dict]):
        grafana_users = {user["userId"]: user for user in api_users}
        existing_user_ids = set(organization.users.all().values_list("user_id", flat=True))

        # create missing users
        users_to_create = tuple(
            User(
                organization_id=organization.pk,
                user_id=user["userId"],
                email=user["email"],
                name=user["name"],
                username=user["login"],
                role=LegacyAccessControlRole[user["role"].upper()],
                avatar_url=user["avatarUrl"],
                permissions=user["permissions"],
            )
            for user in grafana_users.values()
            if user["userId"] not in existing_user_ids
        )
        organization.users.bulk_create(users_to_create, batch_size=5000)

        # delete excess users
        user_ids_to_delete = existing_user_ids - grafana_users.keys()
        organization.users.filter(user_id__in=user_ids_to_delete).delete()

        # update existing users if any fields have changed
        users_to_update = []
        for user in organization.users.filter(user_id__in=existing_user_ids):
            grafana_user = grafana_users[user.user_id]
            g_user_role = LegacyAccessControlRole[grafana_user["role"].upper()]

            if (
                user.email != grafana_user["email"]
                or user.name != grafana_user["name"]
                or user.username != grafana_user["login"]
                or user.role != g_user_role
                or user.avatar_url != grafana_user["avatarUrl"]
                # instead of looping through the array of permission objects, simply take the hash
                # of the string representation of the data structures and compare.
                # Need to first convert the lists of objects to strings because lists/dicts are not hashable
                # (because lists and dicts are not hashable.. as they are mutable)
                # https://stackoverflow.com/a/22003440
                or hash(json.dumps(user.permissions)) != hash(json.dumps(grafana_user["permissions"]))
            ):
                user.email = grafana_user["email"]
                user.name = grafana_user["name"]
                user.username = grafana_user["login"]
                user.role = g_user_role
                user.avatar_url = grafana_user["avatarUrl"]
                user.permissions = grafana_user["permissions"]
                users_to_update.append(user)

        organization.users.bulk_update(
            users_to_update, ["email", "name", "username", "role", "avatar_url", "permissions"], batch_size=5000
        )


class UserQuerySet(models.QuerySet):
    def filter(self, *args, **kwargs):
        return super().filter(*args, **kwargs, is_active=True)

    def filter_with_deleted(self, *args, **kwargs):
        return super().filter(*args, **kwargs)

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
    last_notified_in_escalation_policies: "RelatedManager['EscalationPolicy']"
    notification_policies: "RelatedManager['UserNotificationPolicy']"
    organization: "Organization"
    resolved_alert_groups: "RelatedManager['AlertGroup']"
    schedule_export_token: "RelatedManager['ScheduleExportAuthToken']"
    silenced_alert_groups: "RelatedManager['AlertGroup']"
    slack_user_identity: typing.Optional["SlackUserIdentity"]
    user_schedule_export_token: "RelatedManager['UserScheduleExportAuthToken']"
    wiped_alert_groups: "RelatedManager['AlertGroup']"

    objects = UserManager.from_queryset(UserQuerySet)()

    class Meta:
        # For some reason there are cases when Grafana user gets deleted,
        # and then new Grafana user is created with the same user_id
        # Including is_active to unique_together and setting is_active to None allows to
        # have multiple deleted users with the same user_id, but user_id is unique among active users
        unique_together = ("user_id", "organization", "is_active")

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

    def __str__(self):
        return f"{self.pk}: {self.username}"

    @property
    def available_teams(self):
        if self.role == LegacyAccessControlRole.ADMIN:
            return self.organization.teams.all()
        return self.organization.teams.filter(Q(is_sharing_resources_to_all=True) | Q(users=self)).distinct()

    @property
    def is_authenticated(self):
        return True

    @property
    def avatar_full_url(self):
        return urljoin(self.organization.grafana_url, self.avatar_url)

    @property
    def verified_phone_number(self):
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
    def is_telegram_connected(self):
        return hasattr(self, "telegram_connection")

    def self_or_admin(self, user_to_check, organization) -> bool:
        has_admin_permission = user_is_authorized(user_to_check, [RBACPermission.Permissions.USER_SETTINGS_ADMIN])
        return user_to_check.pk == self.pk or (
            has_admin_permission and organization.pk == user_to_check.organization_id
        )

    @property
    def is_notification_allowed(self):
        return user_is_authorized(self, [RBACPermission.Permissions.NOTIFICATIONS_READ])

    def get_username_with_slack_verbal(self, mention=False):
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
        assert dt.tzinfo == pytz.utc, "dt must be in UTC"

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

    def short(self):
        return {
            "username": self.username,
            "pk": self.public_primary_key,
            "avatar": self.avatar_url,
            "avatar_full": self.avatar_full_url,
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

    @staticmethod
    def build_permissions_query(
        permission: LegacyAccessControlCompatiblePermission, organization
    ) -> typing.Union[PermissionsRegexQuery, RoleInQuery]:
        """
        This method returns a django query filter that is compatible with RBAC
        as well as legacy "basic" role based authorization. If a permission is provided we simply do
        a regex search where the permission column contains the permission value (need to use regex because
        the JSON contains method is not supported by sqlite)

        If RBAC is not supported for the org, we make the assumption that we are looking for any users with AT LEAST
        the fallback role. Ex: if the fallback role were editor than we would get editors and admins.
        """
        if organization.is_rbac_permissions_enabled:
            # https://stackoverflow.com/a/50251879
            return PermissionsRegexQuery(permissions__regex=r".*{0}.*".format(permission.value))
        return RoleInQuery(role__lte=permission.fallback_role.value)


# TODO: check whether this signal can be moved to save method of the model
@receiver(post_save, sender=User)
def listen_for_user_model_save(sender: User, instance: User, created: bool, *args, **kwargs) -> None:
    if created:
        instance.notification_policies.create_default_policies_for_user(instance)
        instance.notification_policies.create_important_policies_for_user(instance)
    drop_cached_ical_for_custom_events_for_organization.apply_async(
        (instance.organization_id,),
    )
