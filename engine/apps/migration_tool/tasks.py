import logging

from celery.utils.log import get_task_logger
from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import exceptions

from apps.alerts.models import Alert, AlertGroup, AlertReceiveChannel, ResolutionNote
from apps.migration_tool.models import AmixrMigrationTaskStatus, LockedAlert
from apps.migration_tool.utils import convert_string_to_datetime, get_data_with_respect_to_pagination
from apps.public_api.serializers import PersonalNotificationRuleSerializer
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def start_migration_from_old_amixr(api_token, organization_id, user_id):
    logger.info(f"Start migration task from amixr for organization {organization_id}")
    users = get_users(organization_id, api_token)

    migrate_schedules_task_id = AmixrMigrationTaskStatus.objects.get_migration_task_id(
        organization_id=organization_id, name=migrate_schedules.name
    )
    migrate_schedules.apply_async(
        (api_token, organization_id, user_id, users),
        task_id=migrate_schedules_task_id,
        countdown=5,
    )

    start_migration_user_data_task_id = AmixrMigrationTaskStatus.objects.get_migration_task_id(
        organization_id=organization_id, name=start_migration_user_data.name
    )
    start_migration_user_data.apply_async(
        (api_token, organization_id, users),
        task_id=start_migration_user_data_task_id,
    )
    logger.info(f"Start 'start_migration_from_old_amixr' task for organization {organization_id}")


def get_users(organization_id, api_token):
    Organization = apps.get_model("user_management", "Organization")
    organization = Organization.objects.get(pk=organization_id)
    # get all users from old amixr
    old_users = get_data_with_respect_to_pagination(api_token, "users")
    old_users_emails = [old_user["email"] for old_user in old_users]
    # find users in Grafana OnCall by email
    grafana_users = organization.users.filter(email__in=old_users_emails).values("email", "id")

    grafana_users_dict = {
        gu["email"]: {
            "id": gu["id"],
        }
        for gu in grafana_users
    }

    users = {}
    for old_user in old_users:
        if old_user["email"] in grafana_users_dict:
            users[old_user["id"]] = grafana_users_dict[old_user["email"]]
            users[old_user["id"]]["old_verified_phone_number"] = old_user.get("verified_phone_number")
            users[old_user["id"]]["old_public_primary_key"] = old_user["id"]

    # Example result:
    # users = {
    #     "OLD_PUBLIC_PK": {
    #         "id": 1,  # user pk in OnCall db
    #         "old_verified_phone_number": "1234",
    #         "old_public_primary_key": "OLD_PUBLIC_PK",
    #     },
    #     ...
    # }
    return users


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def migrate_schedules(api_token, organization_id, user_id, users):
    logger.info(f"Started migration schedules for organization {organization_id}")
    OnCallScheduleICal = apps.get_model("schedules", "OnCallScheduleICal")
    Organization = apps.get_model("user_management", "Organization")
    organization = Organization.objects.get(pk=organization_id)

    schedules = get_data_with_respect_to_pagination(api_token, "schedules")
    existing_schedules_names = set(organization.oncall_schedules.values_list("name", flat=True))
    created_schedules = {}
    for schedule in schedules:
        if not schedule["ical_url"] or schedule["name"] in existing_schedules_names:
            continue

        new_schedule = OnCallScheduleICal(
            organization=organization,
            name=schedule["name"],
            ical_url_primary=schedule["ical_url"],
            team_id=None,
        )

        new_schedule.save()

        created_schedules[schedule["id"]] = {
            "id": new_schedule.pk,
        }
        # Example result:
        # created_schedules = {
        #     "OLD_PUBLIC_PK": {
        #         "id": 1,  # schedule pk in OnCall db
        #     },
        #     ...
        # }

    migrate_integrations_task_id = AmixrMigrationTaskStatus.objects.get_migration_task_id(
        organization_id=organization_id, name=migrate_integrations.name
    )
    migrate_integrations.apply_async(
        (api_token, organization_id, user_id, created_schedules, users), task_id=migrate_integrations_task_id
    )

    current_task_id = migrate_schedules.request.id
    AmixrMigrationTaskStatus.objects.get(task_id=current_task_id).update_status_to_finished()
    logger.info(f"Finished migration schedules for organization {organization_id}")


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def migrate_integrations(api_token, organization_id, user_id, created_schedules, users):
    logger.info(f"Started migration integrations for organization {organization_id}")
    Organization = apps.get_model("user_management", "Organization")
    organization = Organization.objects.get(pk=organization_id)

    integrations = get_data_with_respect_to_pagination(api_token, "integrations")

    existing_integrations_names = set(organization.alert_receive_channels.values_list("verbal_name", flat=True))

    for integration in integrations:
        if integration["name"] in existing_integrations_names:
            continue

        try:
            integration_type = [
                key
                for key, value in AlertReceiveChannel.INTEGRATIONS_TO_REVERSE_URL_MAP.items()
                if value == integration["type"]
            ][0]
        except IndexError:
            continue
        if integration_type not in AlertReceiveChannel.WEB_INTEGRATION_CHOICES:
            continue

        new_integration = AlertReceiveChannel.create(
            organization=organization,
            verbal_name=integration["name"],
            integration=integration_type,
            author_id=user_id,
            slack_title_template=integration["templates"]["slack"]["title"],
            slack_message_template=integration["templates"]["slack"]["message"],
            slack_image_url_template=integration["templates"]["slack"]["image_url"],
            sms_title_template=integration["templates"]["sms"]["title"],
            phone_call_title_template=integration["templates"]["phone_call"]["title"],
            web_title_template=integration["templates"]["web"]["title"],
            web_message_template=integration["templates"]["web"]["message"],
            web_image_url_template=integration["templates"]["web"]["image_url"],
            email_title_template=integration["templates"]["email"]["title"],
            email_message_template=integration["templates"]["email"]["message"],
            telegram_title_template=integration["templates"]["telegram"]["title"],
            telegram_message_template=integration["templates"]["telegram"]["message"],
            telegram_image_url_template=integration["templates"]["telegram"]["image_url"],
            grouping_id_template=integration["templates"]["grouping_key"],
            resolve_condition_template=integration["templates"]["resolve_signal"],
            acknowledge_condition_template=integration["templates"]["acknowledge_signal"],
        )
        # collect integration data in a dict
        integration_data = {
            "id": new_integration.pk,
            "verbal_name": new_integration.verbal_name,
            "old_public_primary_key": integration["id"],
        }

        migrate_routes_task_id = AmixrMigrationTaskStatus.objects.get_migration_task_id(
            organization_id=organization_id, name=migrate_routes.name
        )
        migrate_routes.apply_async(
            (api_token, organization_id, users, created_schedules, integration_data),
            task_id=migrate_routes_task_id,
            countdown=3,
        )

    current_task_id = migrate_integrations.request.id
    AmixrMigrationTaskStatus.objects.get(task_id=current_task_id).update_status_to_finished()
    logger.info(f"Finished migration integrations for organization {organization_id}")


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def migrate_routes(api_token, organization_id, users, created_schedules, integration_data):
    logger.info(f"Start migration routes for organization {organization_id}")
    AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")
    ChannelFilter = apps.get_model("alerts", "ChannelFilter")
    Organization = apps.get_model("user_management", "Organization")
    organization = Organization.objects.get(pk=organization_id)

    integration = AlertReceiveChannel.objects.filter(pk=integration_data["id"]).first()
    if integration:
        url = "routes?integration_id={}".format(integration_data["old_public_primary_key"])
        routes = get_data_with_respect_to_pagination(api_token, url)

        default_route = integration.channel_filters.get(is_default=True)
        existing_chain_names = set(organization.escalation_chains.values_list("name", flat=True))
        existing_route_filtering_term = set(integration.channel_filters.values_list("filtering_term", flat=True))

        for route in routes:
            is_default_route = route["is_the_last_route"]
            filtering_term = route["routing_regex"]

            if is_default_route:
                escalation_chain_name = f"{integration_data['verbal_name'][:90]} - default"
            else:
                if filtering_term in existing_route_filtering_term:
                    continue
                escalation_chain_name = f"{integration_data['verbal_name']} - {filtering_term}"[:100]

            if escalation_chain_name in existing_chain_names:
                escalation_chain = organization.escalation_chains.get(name=escalation_chain_name)
            else:
                escalation_chain = organization.escalation_chains.create(name=escalation_chain_name)

            if is_default_route:
                new_route = default_route
                new_route.escalation_chain = escalation_chain
                new_route.save(update_fields=["escalation_chain"])
            else:
                new_route = ChannelFilter(
                    alert_receive_channel_id=integration_data["id"],
                    escalation_chain_id=escalation_chain.pk,
                    filtering_term=filtering_term,
                    order=route["position"],
                )
                new_route.save()

            route_data = {
                "id": new_route.pk,
                "old_public_primary_key": route["id"],
                "escalation_chain": {
                    "id": escalation_chain.pk,
                },
            }

            migrate_escalation_policies_task_id = AmixrMigrationTaskStatus.objects.get_migration_task_id(
                organization_id=organization_id, name=migrate_escalation_policies.name
            )
            migrate_escalation_policies.apply_async(
                (api_token, organization_id, users, created_schedules, route_data),
                task_id=migrate_escalation_policies_task_id,
                countdown=2,
            )

            start_migration_alert_groups_task_id = AmixrMigrationTaskStatus.objects.get_migration_task_id(
                organization_id=organization_id, name=start_migration_alert_groups.name
            )
            start_migration_alert_groups.apply_async(
                (api_token, organization_id, users, integration_data, route_data),
                task_id=start_migration_alert_groups_task_id,
                countdown=10,
            )

    current_task_id = migrate_routes.request.id
    AmixrMigrationTaskStatus.objects.get(task_id=current_task_id).update_status_to_finished()
    logger.info(f"Finished migration routes for organization {organization_id}")


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def migrate_escalation_policies(api_token, organization_id, users, created_schedules, route_data):
    logger.info(f"Start migration escalation policies for organization {organization_id}")
    EscalationChain = apps.get_model("alerts", "EscalationChain")
    EscalationPolicy = apps.get_model("alerts", "EscalationPolicy")

    escalation_chain = EscalationChain.objects.filter(pk=route_data["escalation_chain"]["id"]).first()
    if escalation_chain and not escalation_chain.escalation_policies.exists():

        url = "escalation_policies?route_id={}".format(route_data["old_public_primary_key"])
        escalation_policies = get_data_with_respect_to_pagination(api_token, url)

        for escalation_policy in escalation_policies:
            try:
                step_type = [
                    key
                    for key, value in EscalationPolicy.PUBLIC_STEP_CHOICES_MAP.items()
                    if value == escalation_policy["type"] and key in EscalationPolicy.PUBLIC_STEP_CHOICES
                ][0]
            except IndexError:
                continue

            if step_type in EscalationPolicy.DEFAULT_TO_IMPORTANT_STEP_MAPPING and escalation_policy.get("important"):
                step_type = EscalationPolicy.DEFAULT_TO_IMPORTANT_STEP_MAPPING[step_type]

            notify_to_users_queue = []

            if step_type == EscalationPolicy.STEP_NOTIFY_USERS_QUEUE:
                notify_to_users_queue = [
                    users[user_old_public_pk]["id"]
                    for user_old_public_pk in escalation_policy.get("persons_to_notify_next_each_time", [])
                    if user_old_public_pk in users
                ]
            elif step_type in [
                EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
                EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT,
            ]:
                notify_to_users_queue = [
                    users[user_old_public_pk]["id"]
                    for user_old_public_pk in escalation_policy.get("persons_to_notify", [])
                    if user_old_public_pk in users
                ]

            if step_type == EscalationPolicy.STEP_NOTIFY_IF_TIME:
                notify_from_time = timezone.datetime.strptime(
                    escalation_policy.get("notify_if_time_from"), "%H:%M:%SZ"
                ).time()
                notify_to_time = timezone.datetime.strptime(
                    escalation_policy.get("notify_if_time_to"), "%H:%M:%SZ"
                ).time()
            else:
                notify_from_time, notify_to_time = None, None
            duration = escalation_policy.get("duration")
            wait_delay = timezone.timedelta(seconds=duration) if duration else None

            schedule_id = escalation_policy.get("notify_on_call_from_schedule")

            notify_schedule_id = created_schedules.get(schedule_id, {}).get("id") if schedule_id else None

            new_escalation_policy = EscalationPolicy(
                step=step_type,
                order=escalation_policy["position"],
                escalation_chain=escalation_chain,
                notify_schedule_id=notify_schedule_id,
                wait_delay=wait_delay,
                from_time=notify_from_time,
                to_time=notify_to_time,
            )

            new_escalation_policy.save()
            if notify_to_users_queue:
                new_escalation_policy.notify_to_users_queue.set(notify_to_users_queue)

    current_task_id = migrate_escalation_policies.request.id
    AmixrMigrationTaskStatus.objects.get(task_id=current_task_id).update_status_to_finished()
    logger.info(f"Finished migration escalation policies for organization {organization_id}")


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def start_migration_alert_groups(api_token, organization_id, users, integration_data, route_data):
    logger.info(f"Start migration alert groups for organization {organization_id}")
    ChannelFilter = apps.get_model("alerts", "ChannelFilter")

    url = "incidents?route_id={}".format(route_data["old_public_primary_key"])
    alert_groups = get_data_with_respect_to_pagination(api_token, url)

    route = ChannelFilter.objects.filter(pk=route_data["id"]).first()

    if route and not route.alert_groups.exists():
        for alert_group in alert_groups:

            migrate_alert_group_task_id = AmixrMigrationTaskStatus.objects.get_migration_task_id(
                organization_id=organization_id, name=migrate_alert_group.name
            )
            migrate_alert_group.apply_async(
                (api_token, organization_id, users, integration_data, route_data, alert_group),
                task_id=migrate_alert_group_task_id,
            )

    current_task_id = start_migration_alert_groups.request.id
    AmixrMigrationTaskStatus.objects.get(task_id=current_task_id).update_status_to_finished()
    logger.info(f"Finished 'start_migration_alert_groups' for organization {organization_id}")


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def migrate_alert_group(api_token, organization_id, users, integration_data, route_data, alert_group_to_migrate):
    logger.info(f"Start migration alert_group {alert_group_to_migrate['id']} for organization {organization_id}")
    integration = AlertReceiveChannel.objects.get(pk=integration_data["id"])
    resolve_by_user_id = None
    acknowledged_by_user_id = None

    if alert_group_to_migrate["resolved_by_user"]:
        resolve_by_user_id = users.get(alert_group_to_migrate["resolved_by_user"], {}).get("id")
    if alert_group_to_migrate["acknowledged_by_user"]:
        acknowledged_by_user_id = users.get(alert_group_to_migrate["acknowledged_by_user"], {}).get("id")

    new_group = AlertGroup.all_objects.create(
        channel=integration,
        channel_filter_id=route_data["id"],
        resolved=True,
        resolved_by=alert_group_to_migrate["resolved_by"],
        resolved_by_user_id=resolve_by_user_id,
        resolved_at=alert_group_to_migrate.get("resolved_at") or timezone.now(),
        acknowledged=alert_group_to_migrate["acknowledged"],
        acknowledged_by=alert_group_to_migrate["acknowledged_by"],
        acknowledged_by_user_id=acknowledged_by_user_id,
        acknowledged_at=alert_group_to_migrate.get("acknowledged_at"),
    )

    new_group.started_at = convert_string_to_datetime(alert_group_to_migrate["created_at"])
    new_group.save(update_fields=["started_at"])

    alert_group_data = {
        "id": new_group.pk,
        "old_public_primary_key": alert_group_to_migrate["id"],
    }

    start_migration_alerts_task_id = AmixrMigrationTaskStatus.objects.get_migration_task_id(
        organization_id=organization_id, name=start_migration_alerts.name
    )
    start_migration_alerts.apply_async(
        (api_token, organization_id, alert_group_data),
        task_id=start_migration_alerts_task_id,
    )

    start_migration_logs_task_id = AmixrMigrationTaskStatus.objects.get_migration_task_id(
        organization_id=organization_id, name=start_migration_logs.name
    )
    start_migration_logs.apply_async(
        (api_token, organization_id, users, alert_group_data),
        task_id=start_migration_logs_task_id,
        countdown=5,
    )

    current_task_id = migrate_alert_group.request.id
    AmixrMigrationTaskStatus.objects.get(task_id=current_task_id).update_status_to_finished()
    logger.info(f"Finished migration alert_group {alert_group_to_migrate['id']} for organization {organization_id}")


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def start_migration_alerts(api_token, organization_id, alert_group_data):
    logger.info(
        f"Start migration alerts for alert_group {alert_group_data['old_public_primary_key']} "
        f"for organization {organization_id}"
    )
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    alert_group = AlertGroup.all_objects.get(pk=alert_group_data["id"])
    if not alert_group.alerts.exists():

        url = "alerts?incident_id={}".format(alert_group_data["old_public_primary_key"])
        alerts = get_data_with_respect_to_pagination(api_token, url)

        for alert in alerts:
            migrate_alerts_task_id = AmixrMigrationTaskStatus.objects.get_migration_task_id(
                organization_id=organization_id, name=migrate_alert.name
            )
            migrate_alert.apply_async(
                (organization_id, alert_group_data, alert),
                task_id=migrate_alerts_task_id,
            )

    current_task_id = start_migration_alerts.request.id
    AmixrMigrationTaskStatus.objects.get(task_id=current_task_id).update_status_to_finished()
    logger.info(
        f"Finished 'start_migration_alerts' for alert_group {alert_group_data['old_public_primary_key']} "
        f"for organization {organization_id}"
    )


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def migrate_alert(organization_id, alert_group_data, alert):
    logger.info(f"Start migration alert {alert['id']} for organization {organization_id}")
    with transaction.atomic():
        new_alert = Alert(
            title=alert["title"],
            message=alert["message"],
            image_url=alert["image_url"],
            link_to_upstream_details=alert["link_to_upstream_details"],
            group_id=alert_group_data["id"],
            integration_unique_data=alert["payload"],
            raw_request_data=alert["payload"],
        )
        new_alert.save()
        LockedAlert.objects.create(alert=new_alert)
        new_alert.created_at = convert_string_to_datetime(alert["created_at"])
        new_alert.save(update_fields=["created_at"])

    current_task_id = migrate_alert.request.id
    AmixrMigrationTaskStatus.objects.get(task_id=current_task_id).update_status_to_finished()
    logger.info(f"Finished migration alert {alert['id']} for organization {organization_id}")


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def start_migration_logs(api_token, organization_id, users, alert_group_data):
    logger.info(f"Start migration logs for alert_group {alert_group_data['id']} for organization {organization_id}")
    url = "incident_logs?incident_id={}".format(alert_group_data["old_public_primary_key"])
    alert_group_logs = get_data_with_respect_to_pagination(api_token, url)

    for log in alert_group_logs:
        migrate_logs_task_id = AmixrMigrationTaskStatus.objects.get_migration_task_id(
            organization_id=organization_id, name=migrate_log.name
        )
        migrate_log.apply_async(
            (organization_id, users, alert_group_data, log),
            task_id=migrate_logs_task_id,
        )

    current_task_id = start_migration_logs.request.id
    AmixrMigrationTaskStatus.objects.get(task_id=current_task_id).update_status_to_finished()
    logger.info(
        f"Finished 'start_migration_logs' for alert_group {alert_group_data['id']} for organization {organization_id}"
    )


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def migrate_log(organization_id, users, alert_group_data, log):
    logger.info(f"Start migration log for alert_group {alert_group_data['id']} for organization {organization_id}")
    log_author_id = users.get(log["author"], {}).get("id")
    new_resolution_note = ResolutionNote(
        author_id=log_author_id,
        message_text=log["text"],
        alert_group_id=alert_group_data["id"],
    )
    new_resolution_note.save()
    new_resolution_note.created_at = convert_string_to_datetime(log["created_at"])
    new_resolution_note.save(update_fields=["created_at"])

    current_task_id = migrate_log.request.id
    AmixrMigrationTaskStatus.objects.get(task_id=current_task_id).update_status_to_finished()


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def start_migration_user_data(api_token, organization_id, users):
    logger.info(f"Start migration user data for organization {organization_id}")
    for user in users:
        user_data = users[user]
        migrate_user_data_task_id = AmixrMigrationTaskStatus.objects.get_migration_task_id(
            organization_id=organization_id, name=migrate_user_data.name
        )
        migrate_user_data.apply_async(
            (api_token, organization_id, user_data),
            task_id=migrate_user_data_task_id,
        )

    current_task_id = start_migration_user_data.request.id
    AmixrMigrationTaskStatus.objects.get(task_id=current_task_id).update_status_to_finished()
    logger.info(f"Finished 'start_migration_user_data' task for organization {organization_id}")


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def migrate_user_data(api_token, organization_id, user_to_migrate):
    logger.info(f"Start migration user {user_to_migrate['id']} for organization {organization_id}")
    User = apps.get_model("user_management", "User")
    UserNotificationPolicy = apps.get_model("base", "UserNotificationPolicy")
    user = User.objects.filter(pk=user_to_migrate["id"], organization_id=organization_id).first()

    if user:
        if not user.verified_phone_number and user_to_migrate["old_verified_phone_number"]:
            user.save_verified_phone_number(user_to_migrate["old_verified_phone_number"])

        url = "personal_notification_rules?user_id={}".format(user_to_migrate["old_public_primary_key"])
        user_notification_policies = get_data_with_respect_to_pagination(api_token, url)

        notification_policies_to_create = []
        existing_notification_policies_ids = list(user.notification_policies.all().values_list("pk", flat=True))

        for notification_policy in user_notification_policies:

            try:
                step, notification_channel = PersonalNotificationRuleSerializer._type_to_step_and_notification_channel(
                    notification_policy["type"],
                )
            except exceptions.ValidationError:
                continue

            new_notification_policy = UserNotificationPolicy(
                user=user,
                important=notification_policy["important"],
                step=step,
                order=notification_policy["position"],
            )
            if step == UserNotificationPolicy.Step.NOTIFY:
                new_notification_policy.notify_by = notification_channel

            if step == UserNotificationPolicy.Step.WAIT:
                duration = notification_policy.get("duration")
                wait_delay = timezone.timedelta(seconds=duration) if duration else UserNotificationPolicy.FIVE_MINUTES
                new_notification_policy.wait_delay = wait_delay

            notification_policies_to_create.append(new_notification_policy)

        UserNotificationPolicy.objects.bulk_create(notification_policies_to_create, batch_size=5000)
        user.notification_policies.filter(pk__in=existing_notification_policies_ids).delete()

    current_task_id = migrate_user_data.request.id
    AmixrMigrationTaskStatus.objects.get(task_id=current_task_id).update_status_to_finished()
    logger.info(f"Finished migration user {user_to_migrate['id']} for organization {organization_id}")
