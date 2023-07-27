import logging
import random
from typing import Optional

from celery import uuid as celery_uuid
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from apps.alerts.tasks.compare_escalations import compare_escalations
from apps.slack.alert_group_slack_service import AlertGroupSlackService
from apps.slack.constants import CACHE_UPDATE_INCIDENT_SLACK_MESSAGE_LIFETIME, SLACK_BOT_ID
from apps.slack.scenarios.scenario_step import ScenarioStep
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import SlackAPIException, SlackAPITokenException
from apps.slack.utils import (
    get_cache_key_update_incident_slack_message,
    get_populate_slack_channel_task_id_key,
    post_message_to_channel,
)
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.utils import batch_queryset

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True)
def update_incident_slack_message(slack_team_identity_pk, alert_group_pk):
    cache_key = get_cache_key_update_incident_slack_message(alert_group_pk)
    cached_task_id = cache.get(cache_key)
    current_task_id = update_incident_slack_message.request.id

    if cached_task_id is None:
        update_task_id = update_incident_slack_message.apply_async(
            (slack_team_identity_pk, alert_group_pk),
            countdown=10,
        )
        cache.set(cache_key, update_task_id, timeout=CACHE_UPDATE_INCIDENT_SLACK_MESSAGE_LIFETIME)

        return (
            f"update_incident_slack_message rescheduled because of current task_id ({current_task_id})"
            f" for alert_group {alert_group_pk} doesn't exist in cache"
        )
    if not current_task_id == cached_task_id:
        return (
            f"update_incident_slack_message skipped, because of current task_id ({current_task_id})"
            f" doesn't equal to cached task_id ({cached_task_id}) for alert_group {alert_group_pk}"
        )

    from apps.alerts.models import AlertGroup
    from apps.slack.models import SlackTeamIdentity

    slack_team_identity = SlackTeamIdentity.objects.get(pk=slack_team_identity_pk)
    alert_group = AlertGroup.objects.get(pk=alert_group_pk)

    if alert_group.skip_escalation_in_slack or alert_group.channel.is_rate_limited_in_slack:
        return "Skip message update in Slack due to rate limit"
    if alert_group.slack_message is None:
        return "Skip message update in Slack due to absence of slack message"
    AlertGroupSlackService(slack_team_identity).update_alert_group_slack_message(alert_group)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True)
def check_slack_message_exists_before_post_message_to_thread(
    alert_group_pk,
    text,
    escalation_policy_pk=None,
    escalation_policy_step=None,
    step_specific_info=None,
):
    """
    Check if slack message for current alert group exists before before posting a message to a thread in slack.
    If it does not exist - restart task every 10 seconds for 24 hours.
    """
    from apps.alerts.models import AlertGroup, AlertGroupLogRecord, EscalationPolicy

    alert_group = AlertGroup.objects.get(pk=alert_group_pk)
    slack_team_identity = alert_group.channel.organization.slack_team_identity
    # get escalation policy object if it exists to save it in log record
    escalation_policy = EscalationPolicy.objects.filter(pk=escalation_policy_pk).first()

    # we cannot post message to thread if team does not have slack team identity
    if not slack_team_identity:
        AlertGroupLogRecord(
            type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
            alert_group=alert_group,
            escalation_policy=escalation_policy,
            escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_NOTIFY_IN_SLACK,
            escalation_policy_step=escalation_policy_step,
            step_specific_info=step_specific_info,
        ).save()
        logger.debug(
            f"Failed to post message to thread in Slack for alert_group {alert_group_pk} because "
            f"slack team identity doesn't exist"
        )
        return
    retry_timeout_hours = 24
    slack_message = alert_group.get_slack_message()

    if slack_message is not None:
        AlertGroupSlackService(slack_team_identity).publish_message_to_alert_group_thread(alert_group, text=text)

    # check how much time has passed since alert group was created
    # to prevent eternal loop of restarting check_slack_message_before_post_message_to_thread
    elif timezone.now() < alert_group.started_at + timezone.timedelta(hours=retry_timeout_hours):
        logger.debug(
            f"check_slack_message_exists_before_post_message_to_thread for alert_group {alert_group.pk} failed "
            f"because slack message does not exist. Restarting check_slack_message_before_post_message_to_thread."
        )
        restart_delay_seconds = 10
        check_slack_message_exists_before_post_message_to_thread.apply_async(
            (
                alert_group_pk,
                text,
                escalation_policy_pk,
                escalation_policy_step,
                step_specific_info,
            ),
            countdown=restart_delay_seconds,
        )
    else:
        logger.debug(
            f"check_slack_message_exists_before_post_message_to_thread for alert_group {alert_group.pk} failed "
            f"because slack message after {retry_timeout_hours} hours still does not exist"
        )
        # create log if it was triggered by escalation step
        if escalation_policy_step:
            AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
                alert_group=alert_group,
                escalation_policy=escalation_policy,
                escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_NOTIFY_IN_SLACK,
                escalation_policy_step=escalation_policy_step,
                step_specific_info=step_specific_info,
            ).save()


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=1)
def send_message_to_thread_if_bot_not_in_channel(alert_group_pk, slack_team_identity_pk, channel_id):
    """
    Send message to alert group's thread if bot is not in current channel
    """

    from apps.alerts.models import AlertGroup
    from apps.slack.models import SlackTeamIdentity

    slack_team_identity = SlackTeamIdentity.objects.get(pk=slack_team_identity_pk)
    alert_group = AlertGroup.objects.get(pk=alert_group_pk)

    sc = SlackClientWithErrorHandling(slack_team_identity.bot_access_token)

    bot_user_id = slack_team_identity.bot_user_id
    members = slack_team_identity.get_conversation_members(sc, channel_id)
    if bot_user_id not in members:
        text = f"Please invite <@{bot_user_id}> to this channel to make all features " f"available :wink:"
        AlertGroupSlackService(slack_team_identity, sc).publish_message_to_alert_group_thread(alert_group, text=text)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=0)
def unpopulate_slack_user_identities(organization_pk, force=False, ts=None):
    from apps.user_management.models import Organization, User

    organization = Organization.objects.get(pk=organization_pk)

    users_to_update = []
    for user in organization.users.filter(slack_user_identity__isnull=False):
        user.slack_user_identity = None
        users_to_update.append(user)

    User.objects.bulk_update(users_to_update, ["slack_user_identity"], batch_size=5000)

    if force:
        organization.slack_team_identity = None
        organization.general_log_channel_id = None
        organization.save()


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=0)
def populate_slack_user_identities(organization_pk):
    from apps.slack.models import SlackUserIdentity
    from apps.user_management.models import Organization

    organization = Organization.objects.get(pk=organization_pk)
    unpopulate_slack_user_identities(organization_pk)
    slack_team_identity = organization.slack_team_identity

    slack_user_identity_installed = slack_team_identity.installed_by
    slack_user_identities_to_update = []

    for member in slack_team_identity.members:
        profile = member.get("profile")
        email = profile.get("email", None)

        # Don't collect bots, invited users and users from other workspaces
        if (
            member.get("id", None) == SLACK_BOT_ID
            or member.get("is_bot", False)
            or not email
            or member.get("is_invited_user", False)
            or member.get("is_restricted")
            or member.get("is_ultra_restricted")
        ):
            continue

        # For user which installs bot
        if member.get("id", None) == slack_user_identity_installed.slack_id:
            slack_user_identity = slack_user_identity_installed
        else:
            try:
                slack_user_identity, _ = slack_team_identity.slack_user_identities.get(
                    slack_id=member["id"],
                )
            except SlackUserIdentity.DoesNotExist:
                continue

        slack_user_identity.cached_slack_login = member.get("name", None)
        slack_user_identity.cached_name = member.get("real_name") or profile.get("real_name", None)
        slack_user_identity.cached_slack_email = profile.get("email", "")

        slack_user_identity.profile_real_name = profile.get("real_name", None)
        slack_user_identity.profile_real_name_normalized = profile.get("real_name_normalized", None)
        slack_user_identity.profile_display_name = profile.get("display_name", None)
        slack_user_identity.profile_display_name_normalized = profile.get("display_name_normalized", None)
        slack_user_identity.cached_avatar = profile.get("image_512", None)
        slack_user_identity.cached_timezone = member.get("tz", None)

        slack_user_identity.deleted = member.get("deleted", None)
        slack_user_identity.is_admin = member.get("is_admin", None)
        slack_user_identity.is_owner = member.get("is_owner", None)
        slack_user_identity.is_primary_owner = member.get("is_primary_owner", None)
        slack_user_identity.is_restricted = member.get("is_restricted", None)
        slack_user_identity.is_ultra_restricted = member.get("is_ultra_restricted", None)
        slack_user_identity.cached_is_bot = member.get("is_bot", None)  # This fields already existed
        slack_user_identity.is_app_user = member.get("is_app_user", None)

        slack_user_identities_to_update.append(slack_user_identity)

    fields_to_update = [
        "cached_slack_login",
        "cached_name",
        "cached_slack_email",
        "profile_real_name",
        "profile_real_name_normalized",
        "profile_display_name",
        "profile_display_name_normalized",
        "cached_avatar",
        "cached_timezone",
        "deleted",
        "is_admin",
        "is_owner",
        "is_primary_owner",
        "is_restricted",
        "is_ultra_restricted",
        "cached_is_bot",
        "is_app_user",
    ]
    SlackUserIdentity.objects.bulk_update(slack_user_identities_to_update, fields_to_update, batch_size=5000)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def post_or_update_log_report_message_task(alert_group_pk, slack_team_identity_pk, update=False):
    logger.debug(f"Start post_or_update_log_report_message_task for alert_group {alert_group_pk}")
    from apps.alerts.models import AlertGroup
    from apps.slack.models import SlackTeamIdentity

    UpdateLogReportMessageStep = ScenarioStep.get_step("distribute_alerts", "UpdateLogReportMessageStep")

    slack_team_identity = SlackTeamIdentity.objects.get(pk=slack_team_identity_pk)
    alert_group = AlertGroup.objects.get(pk=alert_group_pk)
    step = UpdateLogReportMessageStep(slack_team_identity, alert_group.channel.organization)

    if alert_group.skip_escalation_in_slack or alert_group.channel.is_rate_limited_in_slack:
        return

    if update:  # flag to prevent multiple posting log message to slack
        step.update_log_message(alert_group)
    else:
        step.post_log_message(alert_group)
    logger.debug(f"Finish post_or_update_log_report_message_task for alert_group {alert_group_pk}")


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def post_slack_rate_limit_message(integration_id):
    from apps.alerts.models import AlertReceiveChannel

    try:
        integration = AlertReceiveChannel.objects.get(pk=integration_id)
    except AlertReceiveChannel.DoesNotExist:
        logger.warning(f"AlertReceiveChannel {integration_id} doesn't exist")
        return

    if not compare_escalations(post_slack_rate_limit_message.request.id, integration.rate_limit_message_task_id):
        logger.info(
            f"post_slack_rate_limit_message. integration {integration_id}. ID mismatch. "
            f"Active: {integration.rate_limit_message_task_id}"
        )
        return
    default_route = integration.channel_filters.get(is_default=True)
    slack_channel = default_route.slack_channel_id_or_general_log_id
    if slack_channel:
        text = (
            f"Delivering and updating alert groups of integration {integration.verbal_name} in Slack is "
            f"temporarily stopped due to rate limit. You could find new alert groups at "
            f"<{integration.new_incidents_web_link}|web page "
            '"Alert Groups">'
        )
        post_message_to_channel(integration.organization, slack_channel, text)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def populate_slack_usergroups():
    from apps.slack.models import SlackTeamIdentity

    slack_team_identities = SlackTeamIdentity.objects.filter(
        detected_token_revoked__isnull=True,
    )

    delay = 0
    counter = 0

    for qs in batch_queryset(slack_team_identities, 5000):
        for slack_team_identity in qs:
            counter += 1
            # increase delay to prevent slack ratelimit
            if counter % 8 == 0:
                delay += 60
            populate_slack_usergroups_for_team.apply_async((slack_team_identity.pk,), countdown=delay)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def populate_slack_usergroups_for_team(slack_team_identity_id):
    from apps.slack.models import SlackTeamIdentity, SlackUserGroup

    slack_team_identity = SlackTeamIdentity.objects.get(pk=slack_team_identity_id)
    sc = SlackClientWithErrorHandling(slack_team_identity.bot_access_token)

    def handle_usergroups_list_slack_api_exception(exception):
        if exception.response["error"] == "plan_upgrade_required":
            logger.info(f"SlackTeamIdentity with pk {slack_team_identity.pk} does not have access to User Groups")
        elif exception.response["error"] == "invalid_auth":
            logger.warning(f"invalid_auth, SlackTeamIdentity pk: {slack_team_identity.pk}")
        # in some cases slack rate limit error looks like 'rate_limited', in some - 'ratelimited', be aware
        elif exception.response["error"] == "rate_limited" or exception.response["error"] == "ratelimited":
            delay = random.randint(5, 25) * 60
            logger.warning(
                f"'usergroups.list' slack api error: rate_limited. SlackTeamIdentity pk: {slack_team_identity.pk}."
                f"Delay populate_slack_usergroups_for_team task by {delay // 60} min."
            )
            return populate_slack_usergroups_for_team.apply_async((slack_team_identity_id,), countdown=delay)
        elif exception.response["error"] == "missing_scope":
            logger.warning(
                f"'usergroups.users.list' slack api error: missing_scope. "
                f"SlackTeamIdentity pk: {slack_team_identity.pk}.\n{exception}"
            )
            return
        else:
            logger.error(
                f"'usergroups.list' slack api error. SlackTeamIdentity pk: {slack_team_identity.pk}\n{exception}"
            )
            raise exception

    usergroups_list = None
    bot_access_token_accepted = True
    try:
        usergroups_list = sc.api_call(
            "usergroups.list",
        )
    except SlackAPITokenException as e:
        logger.info(f"token revoked\n{e}")
    except SlackAPIException as e:
        if e.response["error"] == "not_allowed_token_type":
            try:
                # Trying same request with access token. It is required due to migration to granular permissions
                # and can be removed after clients reinstall their bots
                sc_with_access_token = SlackClientWithErrorHandling(slack_team_identity.access_token)
                usergroups_list = sc_with_access_token.api_call(
                    "usergroups.list",
                )
                bot_access_token_accepted = False
            except SlackAPIException as err:
                handle_usergroups_list_slack_api_exception(err)
        else:
            handle_usergroups_list_slack_api_exception(e)
    if usergroups_list is not None:
        today = timezone.now().date()
        populated_user_groups_ids = slack_team_identity.usergroups.filter(last_populated=today).values_list(
            "slack_id", flat=True
        )

        for usergroup in usergroups_list["usergroups"]:
            # skip groups that were recently populated
            if usergroup["id"] in populated_user_groups_ids:
                continue
            try:
                if bot_access_token_accepted:
                    usergroups_users = sc.api_call(
                        "usergroups.users.list",
                        usergroup=usergroup["id"],
                    )
                else:
                    sc_with_access_token = SlackClientWithErrorHandling(slack_team_identity.access_token)
                    usergroups_users = sc_with_access_token.api_call(
                        "usergroups.users.list",
                        usergroup=usergroup["id"],
                    )
            except SlackAPIException as e:
                if e.response["error"] == "no_such_subteam":
                    logger.info("User group does not exist")
                elif e.response["error"] == "missing_scope":
                    logger.warning(
                        f"'usergroups.users.list' slack api error: missing_scope. "
                        f"SlackTeamIdentity pk: {slack_team_identity.pk}.\n{e}"
                    )
                    return
                elif e.response["error"] == "invalid_auth":
                    logger.warning(f"invalid_auth, SlackTeamIdentity pk: {slack_team_identity.pk}")
                # in some cases slack rate limit error looks like 'rate_limited', in some - 'ratelimited', be aware
                elif e.response["error"] == "rate_limited" or e.response["error"] == "ratelimited":
                    delay = random.randint(5, 25) * 60
                    logger.warning(
                        f"'usergroups.users.list' slack api error: rate_limited. "
                        f"SlackTeamIdentity pk: {slack_team_identity.pk}."
                        f"Delay populate_slack_usergroups_for_team task by {delay // 60} min."
                    )
                    return populate_slack_usergroups_for_team.apply_async((slack_team_identity_id,), countdown=delay)
                else:
                    logger.error(
                        f"'usergroups.users.list' slack api error. "
                        f"SlackTeamIdentity pk: {slack_team_identity.pk}\n{e}"
                    )
                    raise e
            else:
                usergroup_name = usergroup["name"]
                usergroup_handle = usergroup["handle"]
                usergroup_members = usergroups_users["users"]
                usergroup_is_active = usergroup["date_delete"] == 0

                SlackUserGroup.objects.update_or_create(
                    slack_id=usergroup["id"],
                    slack_team_identity=slack_team_identity,
                    defaults={
                        "name": usergroup_name,
                        "handle": usergroup_handle,
                        "members": usergroup_members,
                        "is_active": usergroup_is_active,
                        "last_populated": today,
                    },
                )


@shared_dedicated_queue_retry_task()
def start_update_slack_user_group_for_schedules():
    from apps.slack.models import SlackUserGroup

    user_group_pks = (
        SlackUserGroup.objects.filter(oncall_schedules__isnull=False).distinct().values_list("pk", flat=True)
    )

    for user_group_pk in user_group_pks:
        update_slack_user_group_for_schedules.delay(user_group_pk=user_group_pk)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def update_slack_user_group_for_schedules(user_group_pk):
    from apps.slack.models import SlackUserGroup

    try:
        user_group = SlackUserGroup.objects.get(pk=user_group_pk)
    except SlackUserGroup.DoesNotExist:
        logger.warning(f"Slack user group {user_group_pk} does not exist")
        return

    user_group.update_oncall_members()


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def populate_slack_channels():
    from apps.slack.models import SlackTeamIdentity

    slack_team_identities = SlackTeamIdentity.objects.filter(
        detected_token_revoked__isnull=True,
    )

    delay = 0
    counter = 0

    for qs in batch_queryset(slack_team_identities, 5000):
        for slack_team_identity in qs:
            counter += 1
            # increase delay to prevent slack ratelimit
            if counter % 8 == 0:
                delay += 60
            start_populate_slack_channels_for_team(slack_team_identity.pk, delay)


def start_populate_slack_channels_for_team(
    slack_team_identity_id: int, delay: int, cursor: Optional[str] = None
) -> None:
    # save active task id in cache to make only one populate task active per team
    task_id = celery_uuid()
    cache_key = get_populate_slack_channel_task_id_key(slack_team_identity_id)
    cache.set(cache_key, task_id)
    populate_slack_channels_for_team.apply_async((slack_team_identity_id, cursor), countdown=delay, task_id=task_id)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def populate_slack_channels_for_team(slack_team_identity_id: int, cursor: Optional[str] = None) -> None:
    """
    Make paginated request to get slack channels. On ratelimit - update info for got channels, save collected channels
    ids in cache and restart the task with the last successful pagination cursor to avoid any data loss during delay
    time.
    """
    from apps.slack.models import SlackChannel, SlackTeamIdentity

    slack_team_identity = SlackTeamIdentity.objects.get(pk=slack_team_identity_id)
    sc = SlackClientWithErrorHandling(slack_team_identity.bot_access_token)

    active_task_id_key = get_populate_slack_channel_task_id_key(slack_team_identity_id)
    active_task_id = cache.get(active_task_id_key)
    current_task_id = populate_slack_channels_for_team.request.id
    if active_task_id and active_task_id != current_task_id:
        logger.info(
            f"Stop populate_slack_channels_for_team for SlackTeamIdentity pk: {slack_team_identity_id} due to "
            f"incorrect active task id"
        )
        return
    collected_channels_key = f"SLACK_CHANNELS_TEAM_{slack_team_identity_id}"
    collected_channels = cache.get(collected_channels_key, set())
    if cursor and not collected_channels:
        # means the task was restarted after rate limit exception but collected channels were lost
        logger.warning(
            f"Restart slack channel sync for SlackTeamIdentity pk: {slack_team_identity_id} due to empty "
            f"'collected_channels' after rate limit"
        )
        delay = 60
        return start_populate_slack_channels_for_team(slack_team_identity_id, delay)
    try:
        response, cursor, rate_limited = sc.paginated_api_call_with_ratelimit(
            "conversations.list",
            types="public_channel,private_channel",
            paginated_key="channels",
            limit=1000,
            cursor=cursor,
        )
    except SlackAPITokenException as e:
        logger.info(f"token revoked\n{e}")
    except SlackAPIException as e:
        if e.response["error"] == "invalid_auth":
            logger.warning(
                f"invalid_auth while populating slack channels, SlackTeamIdentity pk: {slack_team_identity.pk}"
            )
        elif e.response["error"] == "missing_scope":
            logger.warning(
                f"conversations.list' slack api error: missing_scope. "
                f"SlackTeamIdentity pk: {slack_team_identity.pk}.\n{e}"
            )
        else:
            logger.error(f"'conversations.list' slack api error. SlackTeamIdentity pk: {slack_team_identity.pk}\n{e}")
            raise e
    else:
        today = timezone.now().date()

        slack_channels = {channel["id"]: channel for channel in response["channels"]}
        collected_channels.update(slack_channels.keys())

        existing_channels = slack_team_identity.cached_channels.all()
        existing_channel_ids = set(existing_channels.values_list("slack_id", flat=True))

        # create missing channels
        channels_to_create = tuple(
            SlackChannel(
                slack_team_identity=slack_team_identity,
                slack_id=channel["id"],
                name=channel["name"],
                is_archived=channel["is_archived"],
                is_shared=channel["is_shared"],
                last_populated=today,
            )
            for channel in slack_channels.values()
            if channel["id"] not in existing_channel_ids
        )
        SlackChannel.objects.bulk_create(channels_to_create, batch_size=5000)

        # update existing channels
        channels_to_update = existing_channels.filter(slack_id__in=slack_channels.keys()).exclude(last_populated=today)
        for channel in channels_to_update:
            slack_channel = slack_channels[channel.slack_id]
            channel.name = slack_channel["name"]
            channel.is_archived = slack_channel["is_archived"]
            channel.is_shared = slack_channel["is_shared"]
            channel.last_populated = today

        SlackChannel.objects.bulk_update(
            channels_to_update, fields=("name", "is_archived", "is_shared", "last_populated"), batch_size=5000
        )
        if rate_limited:
            # save collected channels ids to cache and restart the task with the current pagination cursor
            cache.set(collected_channels_key, collected_channels, timeout=3600)
            delay = random.randint(1, 3) * 60
            logger.warning(
                f"'conversations.list' slack api error: rate_limited. SlackTeamIdentity pk: {slack_team_identity_id}. "
                f"Delay populate_slack_channels_for_team task for {delay//60} min."
            )
            start_populate_slack_channels_for_team(slack_team_identity_id, delay, cursor)
        else:
            # delete excess channels
            assert collected_channels
            channel_ids_to_delete = existing_channel_ids - collected_channels
            slack_team_identity.cached_channels.filter(slack_id__in=channel_ids_to_delete).delete()
            cache.delete(collected_channels_key)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=0)
def clean_slack_integration_leftovers(organization_id, *args, **kwargs):
    """
    This task removes binding to slack (e.g ChannelFilter's slack channel) for a given organization.
    It is used when user changes slack integration.
    """
    from apps.alerts.models import ChannelFilter
    from apps.schedules.models import OnCallSchedule

    logger.info(f"Start clean slack leftovers for organization {organization_id}")
    ChannelFilter.objects.filter(alert_receive_channel__organization_id=organization_id).update(slack_channel_id=None)
    logger.info(f"Cleaned ChannelFilters slack_channel_id for organization {organization_id}")
    OnCallSchedule.objects.filter(organization_id=organization_id).update(channel=None)
    logger.info(f"Cleaned OnCallSchedule slack_channel_id for organization {organization_id}")
    logger.info(f"Finish clean slack leftovers for organization {organization_id}")


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=10)
def clean_slack_channel_leftovers(slack_team_identity_id, slack_channel_id):
    """
    This task removes binding to slack channel after channel arcived or deleted in slack.
    """
    from apps.alerts.models import ChannelFilter
    from apps.slack.models import SlackTeamIdentity
    from apps.user_management.models import Organization

    try:
        sti = SlackTeamIdentity.objects.get(id=slack_team_identity_id)
    except SlackTeamIdentity.DoesNotExist:
        logger.info(
            f"Failed to clean_slack_channel_leftovers slack_channel_id={slack_channel_id} slack_team_identity_id={slack_team_identity_id} : Invalid slack_team_identity_id"
        )
        return

    orgs_to_clean_general_log_channel_id = []
    for org in sti.organizations.all():
        if org.general_log_channel_id == slack_channel_id:
            logger.info(
                f"Set general_log_channel_id to None for org_id={org.id}  slack_channel_id={slack_channel_id} since slack_channel is arcived or deleted"
            )
            org.general_log_channel_id = None
            orgs_to_clean_general_log_channel_id.append(org)
        ChannelFilter.objects.filter(alert_receive_channel__organization=org, slack_channel_id=slack_channel_id).update(
            slack_channel_id=None
        )

    Organization.objects.bulk_update(orgs_to_clean_general_log_channel_id, ["general_log_channel_id"], batch_size=5000)
