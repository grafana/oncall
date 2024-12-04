import logging
import random
import typing

from celery import uuid as celery_uuid
from celery.exceptions import Retry
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from apps.slack.alert_group_slack_service import AlertGroupSlackService
from apps.slack.client import SlackClient
from apps.slack.constants import SLACK_BOT_ID
from apps.slack.errors import (
    SlackAPICantUpdateMessageError,
    SlackAPIChannelInactiveError,
    SlackAPIChannelNotFoundError,
    SlackAPIInvalidAuthError,
    SlackAPIMessageNotFoundError,
    SlackAPIPlanUpgradeRequiredError,
    SlackAPIRatelimitError,
    SlackAPITokenError,
    SlackAPIUsergroupNotFoundError,
)
from apps.slack.utils import get_populate_slack_channel_task_id_key, post_message_to_channel
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.utils import batch_queryset

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True)
def update_alert_group_slack_message(slack_message_pk: int) -> None:
    """
    Background task to update the Slack message for an alert group.

    This function is intended to be executed as a Celery task. It performs the following:
    - Compares the current task ID with the task ID stored in the cache.
      - If they do not match, it means a newer task has been scheduled, so the current task exits to prevent duplicated updates.
    - Does the actual update of the Slack message.
    - Upon successful completion, clears the task ID from the cache to allow future updates (also note that
    the task ID is set in the cache with a timeout, so it will be automatically cleared after a certain period, even
    if this task fails to clear it. See `SlackMessage.update_alert_groups_message` for more details).

    Args:
        slack_message_pk (int): The primary key of the `SlackMessage` instance to update.
    """
    from apps.slack.models import SlackMessage

    current_task_id = update_alert_group_slack_message.request.id

    logger.info(
        f"update_alert_group_slack_message for slack message {slack_message_pk} started with task_id {current_task_id}"
    )

    try:
        slack_message = SlackMessage.objects.get(pk=slack_message_pk)
    except SlackMessage.DoesNotExist:
        logger.warning(f"SlackMessage {slack_message_pk} doesn't exist")
        return

    active_update_task_id = slack_message.get_active_update_task_id()
    if current_task_id != active_update_task_id:
        logger.warning(
            f"update_alert_group_slack_message skipped, because current_task_id ({current_task_id}) "
            f"does not equal to active_update_task_id ({active_update_task_id}) "
        )
        return

    alert_group = slack_message.alert_group
    if not alert_group:
        logger.warning(
            f"skipping update_alert_group_slack_message as SlackMessage {slack_message_pk} "
            "doesn't have an alert group associated with it"
        )
        return

    alert_group_pk = alert_group.pk
    alert_receive_channel = alert_group.channel
    alert_receive_channel_is_rate_limited = alert_receive_channel.is_rate_limited_in_slack

    if alert_group.skip_escalation_in_slack:
        logger.warning(
            f"skipping update_alert_group_slack_message as AlertGroup {alert_group_pk} "
            "has skip_escalation_in_slack set to True"
        )
        return
    elif alert_receive_channel_is_rate_limited:
        logger.warning(
            f"skipping update_alert_group_slack_message as AlertGroup {alert_group.pk}'s "
            f"integration ({alert_receive_channel.pk}) is rate-limited"
        )
        return

    slack_client = SlackClient(slack_message.slack_team_identity)

    try:
        slack_client.chat_update(
            channel=slack_message.channel.slack_id,
            ts=slack_message.slack_id,
            attachments=alert_group.render_slack_attachments(),
            blocks=alert_group.render_slack_blocks(),
        )

        logger.info(f"Message has been updated for alert_group {alert_group_pk}")
    except SlackAPIRatelimitError as e:
        if not alert_receive_channel.is_maintenace_integration:
            if not alert_receive_channel_is_rate_limited:
                alert_receive_channel.start_send_rate_limit_message_task("Updating", e.retry_after)
                logger.info(f"Message has not been updated for alert_group {alert_group_pk} due to slack rate limit.")
        else:
            raise
    except (
        SlackAPIMessageNotFoundError,
        SlackAPICantUpdateMessageError,
        SlackAPIChannelInactiveError,
        SlackAPITokenError,
        SlackAPIChannelNotFoundError,
    ):
        pass

    slack_message.mark_active_update_task_as_complete()


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

    if alert_group.slack_message:
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


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    dont_autoretry_for=(Retry,),
    retry_backoff=True,
    max_retries=1,
)
def send_message_to_thread_if_bot_not_in_channel(
    alert_group_pk: int, slack_team_identity_pk: int, channel_id: int
) -> None:
    """
    Send message to alert group's thread if bot is not in current channel
    """
    from apps.alerts.models import AlertGroup
    from apps.slack.models import SlackTeamIdentity

    logger.info(
        f"Starting send_message_to_thread_if_bot_not_in_channel alert_group={alert_group_pk} "
        f"slack_team_identity={slack_team_identity_pk} channel_id={channel_id}"
    )

    slack_team_identity = SlackTeamIdentity.objects.get(pk=slack_team_identity_pk)
    alert_group = AlertGroup.objects.get(pk=alert_group_pk)

    sc = SlackClient(slack_team_identity, enable_ratelimit_retry=True)

    bot_user_id = slack_team_identity.bot_user_id
    members = slack_team_identity.get_conversation_members(sc, channel_id)
    if bot_user_id not in members:
        text = f"Please invite <@{bot_user_id}> to this channel to make all features available :wink:"

        try:
            logger.info("Attempting to send message to thread in Slack")

            AlertGroupSlackService(slack_team_identity, sc).publish_message_to_alert_group_thread(
                alert_group, text=text
            )
        except SlackAPIRatelimitError as e:
            logger.warning(f"Slack API rate limit error: {e}, retrying task")

            raise send_message_to_thread_if_bot_not_in_channel.retry(
                (alert_group_pk, slack_team_identity_pk, channel_id), countdown=e.retry_after, exc=e
            )


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=0)
def unpopulate_slack_user_identities(organization_pk, force=False, ts=None):
    from apps.user_management.models import Organization, User

    organization = Organization.objects.get(pk=organization_pk)

    # Reset slack_user_identity for organization users (make sure to include deleted users in the queryset)
    User.objects.filter_with_deleted(organization=organization).update(slack_user_identity=None)

    if force:
        organization.slack_team_identity = None
        organization.default_slack_channel = None
        organization.save(update_fields=["slack_team_identity", "default_slack_channel"])


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
def post_slack_rate_limit_message(integration_id: int, error_message_verb: typing.Optional[str] = None) -> None:
    """
    NOTE: error_message_verb was added to the function signature to allow for more descriptive error messages.

    We set it to None by default to maintain backwards compatibility with existing tasks. The default of None
    can likely be removed in the near future (once existing tasks on the queue have been processed).
    """
    from apps.alerts.models import AlertReceiveChannel

    try:
        integration = AlertReceiveChannel.objects.get(pk=integration_id)
    except AlertReceiveChannel.DoesNotExist:
        logger.warning(f"AlertReceiveChannel {integration_id} doesn't exist")
        return

    if post_slack_rate_limit_message.request.id != integration.rate_limit_message_task_id:
        logger.info(
            f"post_slack_rate_limit_message. integration {integration_id}. ID mismatch. "
            f"Active: {integration.rate_limit_message_task_id}"
        )
        return

    default_route = integration.channel_filters.get(is_default=True)
    if (slack_channel := default_route.slack_channel_or_org_default) is not None:
        # NOTE: see function docstring above 👆
        if error_message_verb is None:
            error_message_verb = "Sending messages for"

        text = (
            f"{error_message_verb} Alert Groups in Slack, for integration {integration.verbal_name}, is "
            f"temporarily rate-limited (due to a Slack rate-limit). Meanwhile, you can still find new Alert Groups "
            f'in the <{integration.new_incidents_web_link}|"Alert Groups" web page>'
        )
        post_message_to_channel(integration.organization, slack_channel.slack_id, text)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def populate_slack_usergroups():
    from apps.slack.models import SlackTeamIdentity

    slack_team_identities = SlackTeamIdentity.objects.filter(detected_token_revoked__isnull=True)

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
    sc = SlackClient(slack_team_identity, enable_ratelimit_retry=True)

    try:
        usergroups = sc.usergroups_list()["usergroups"]
    except SlackAPIRatelimitError as e:
        populate_slack_usergroups_for_team.apply_async((slack_team_identity_id,), countdown=e.retry_after)
        return
    except (SlackAPITokenError, SlackAPIInvalidAuthError, SlackAPIPlanUpgradeRequiredError):
        return

    today = timezone.now().date()
    populated_user_groups_ids = slack_team_identity.usergroups.filter(last_populated=today).values_list(
        "slack_id", flat=True
    )

    for usergroup in usergroups:
        # skip groups that were recently populated
        if usergroup["id"] in populated_user_groups_ids:
            continue

        try:
            members = sc.usergroups_users_list(usergroup=usergroup["id"])["users"]
        except SlackAPIRatelimitError as e:
            populate_slack_usergroups_for_team.apply_async((slack_team_identity_id,), countdown=e.retry_after)
            return
        except (SlackAPIUsergroupNotFoundError, SlackAPIInvalidAuthError):
            return

        SlackUserGroup.objects.update_or_create(
            slack_id=usergroup["id"],
            slack_team_identity=slack_team_identity,
            defaults={
                "name": usergroup["name"],
                "handle": usergroup["handle"],
                "members": members,
                "is_active": usergroup["date_delete"] == 0,
                "last_populated": today,
            },
        )


@shared_dedicated_queue_retry_task()
def start_update_slack_user_group_for_schedules():
    from apps.slack.models import SlackUserGroup

    user_group_pks = (
        SlackUserGroup.objects.filter(
            oncall_schedules__isnull=False,  # has oncall schedules connected
            oncall_schedules__organization__deleted_at__isnull=True,  # organization is not deleted
        )
        .distinct()
        .values_list("pk", flat=True)
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

    slack_team_identities = SlackTeamIdentity.objects.filter(detected_token_revoked__isnull=True)

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
    slack_team_identity_id: int, delay: int, cursor: typing.Optional[str] = None
) -> None:
    # save active task id in cache to make only one populate task active per team
    task_id = celery_uuid()
    cache_key = get_populate_slack_channel_task_id_key(slack_team_identity_id)
    cache.set(cache_key, task_id)
    populate_slack_channels_for_team.apply_async((slack_team_identity_id, cursor), countdown=delay, task_id=task_id)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def populate_slack_channels_for_team(slack_team_identity_id: int, cursor: typing.Optional[str] = None) -> None:
    """
    Make paginated request to get slack channels. On ratelimit - update info for got channels, save collected channels
    ids in cache and restart the task with the last successful pagination cursor to avoid any data loss during delay
    time.
    """
    from apps.slack.models import SlackChannel, SlackTeamIdentity

    slack_team_identity = SlackTeamIdentity.objects.get(pk=slack_team_identity_id)
    sc = SlackClient(slack_team_identity, enable_ratelimit_retry=True)

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
            "conversations_list",
            paginated_key="channels",
            types="public_channel,private_channel",
            limit=1000,
            cursor=cursor,
        )
    except (SlackAPITokenError, SlackAPIInvalidAuthError):
        return
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
def clean_slack_integration_leftovers(organization_id: int, *args, **kwargs) -> None:
    """
    This task removes binding to slack (e.g ChannelFilter's slack channel) for a given organization.
    It is used when user changes slack integration.
    """
    from apps.alerts.models import ChannelFilter
    from apps.schedules.models import OnCallSchedule

    logger.info(f"Cleaning up for organization {organization_id}")
    ChannelFilter.objects.filter(alert_receive_channel__organization_id=organization_id).update(slack_channel=None)
    OnCallSchedule.objects.filter(organization_id=organization_id).update(slack_channel=None, user_group=None)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=10)
def clean_slack_channel_leftovers(slack_team_identity_id: int, slack_channel_id: str) -> None:
    """
    This task removes binding to slack channel after a channel is archived in Slack.

    **NOTE**: this is only needed for Slack Channel archive. If a channel is deleted, we simply remove references
    to that channel via `on_delete=models.SET_NULL`.
    """
    from apps.alerts.models import ChannelFilter
    from apps.schedules.models import OnCallSchedule
    from apps.slack.models import SlackTeamIdentity
    from apps.user_management.models import Organization

    orgs_to_clean_default_slack_channel: typing.List[Organization] = []

    try:
        sti = SlackTeamIdentity.objects.get(id=slack_team_identity_id)
    except SlackTeamIdentity.DoesNotExist:
        logger.info(
            f"Failed to clean_slack_channel_leftovers slack_channel_id={slack_channel_id} slack_team_identity_id={slack_team_identity_id} : Invalid slack_team_identity_id"
        )
        return

    for org in sti.organizations.all():
        org_id = org.id

        if org.default_slack_channel_slack_id == slack_channel_id:
            logger.info(
                f"Set default_slack_channel to None for org_id={org_id} slack_channel_id={slack_channel_id} since slack_channel is arcived or deleted"
            )
            org.default_slack_channel = None
            orgs_to_clean_default_slack_channel.append(org)

        # The channel no longer exists, so update any integration routes (ie. ChannelFilter) or schedules
        # that reference it
        ChannelFilter.objects.filter(
            alert_receive_channel__organization=org,
            slack_channel__slack_id=slack_channel_id,
        ).update(slack_channel=None)

        OnCallSchedule.objects.filter(
            organization_id=org_id,
            slack_channel__slack_id=slack_channel_id,
        ).update(slack_channel=None)

    Organization.objects.bulk_update(orgs_to_clean_default_slack_channel, ["default_slack_channel"], batch_size=5000)
