import logging

from django.conf import settings

from apps.alerts.incident_appearance.renderers.constants import DEFAULT_BACKUP_TITLE
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.incident_api.client import (
    DEFAULT_INCIDENT_SEVERITY,
    DEFAULT_INCIDENT_STATUS,
    IncidentAPIClient,
    IncidentAPIException,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 1 if settings.DEBUG else 10
MAX_ATTACHED_ALERT_GROUPS_PER_INCIDENT = 5


def _attach_alert_group_to_incident(alert_group, incident_id, incident_title, escalation_policy, attached=False):
    from apps.alerts.models import AlertGroupLogRecord, DeclaredIncident, EscalationPolicy

    declared_incident, _ = DeclaredIncident.objects.get_or_create(
        incident_id=incident_id,
        defaults={
            "organization": alert_group.channel.organization,
            "channel_filter": alert_group.channel_filter,
        },
    )
    alert_group.declared_incident = declared_incident
    alert_group.save(update_fields=["declared_incident"])
    reason = "attached to existing incident" if attached else "incident declared"
    AlertGroupLogRecord.objects.create(
        type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
        reason=reason,
        alert_group=alert_group,
        step_specific_info={"incident_id": incident_id, "incident_title": incident_title},
        escalation_policy=escalation_policy,
        escalation_policy_step=EscalationPolicy.STEP_DECLARE_INCIDENT,
    )


def _create_error_log_record(alert_group, escalation_policy, reason=""):
    from apps.alerts.models import AlertGroupLogRecord, EscalationPolicy

    AlertGroupLogRecord.objects.create(
        type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED,
        escalation_error_code=AlertGroupLogRecord.ERROR_ESCALATION_INCIDENT_COULD_NOT_BE_DECLARED,
        reason=reason,
        alert_group=alert_group,
        escalation_policy=escalation_policy,
        escalation_policy_step=EscalationPolicy.STEP_DECLARE_INCIDENT,
    )


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def declare_incident(alert_group_pk, escalation_policy_pk):
    from apps.alerts.models import AlertGroup, DeclaredIncident, EscalationPolicy

    alert_group = AlertGroup.objects.get(pk=alert_group_pk)
    organization = alert_group.channel.organization
    escalation_policy = None
    if escalation_policy_pk:
        escalation_policy = EscalationPolicy.objects.filter(pk=escalation_policy_pk).first()

    if alert_group.channel_filter.is_default:
        _create_error_log_record(
            alert_group, escalation_policy, reason="Declare incident step is not enabled for default routes"
        )
        return
    if declare_incident.request.retries == MAX_RETRIES:
        _create_error_log_record(alert_group, escalation_policy)
        return

    incident_client = IncidentAPIClient(organization.grafana_url, organization.api_token)

    # check for currently active related incident in the same route (channel_filter)
    existing_incident = (
        DeclaredIncident.objects.filter(
            organization=organization, channel_filter=alert_group.channel_filter, is_opened=True
        )
        .order_by("-created_at")
        .first()
    )

    if existing_incident:
        incident_id = existing_incident.incident_id
        try:
            # get existing incident details
            incident_data, _ = incident_client.get_incident(incident_id)
        except IncidentAPIException as e:
            logger.error(f"Error getting incident details: {e.msg}")
            if e.status == 404:
                # incident not found, mark as not opened
                existing_incident.is_opened = False
                existing_incident.save(update_fields=["is_opened"])
            else:
                # raise (and retry)
                raise
        else:
            # incident exists, check if it is still active
            if incident_data["status"] == DEFAULT_INCIDENT_STATUS:
                # attach to incident context
                incident_title = incident_data["title"]
                num_attached = AlertGroup.objects.filter(declared_incident=existing_incident).count()
                if num_attached < MAX_ATTACHED_ALERT_GROUPS_PER_INCIDENT:
                    try:
                        incident_data, _ = incident_client.add_activity(incident_id, alert_group.web_link)
                    except IncidentAPIException as e:
                        logger.error(f"Error attaching to existing incident: {e.msg}")
                # setup association between alert group and incident (even if not attached)
                _attach_alert_group_to_incident(
                    alert_group, incident_id, incident_title, escalation_policy, attached=True
                )
            else:
                existing_incident.is_opened = False
                existing_incident.save(update_fields=["is_opened"])

    if existing_incident is None or not existing_incident.is_opened:
        # create new incident
        # TODO: get severity from policy? alert group label?
        try:
            incident_data, _ = incident_client.create_incident(
                alert_group.web_title_cache if alert_group.web_title_cache else DEFAULT_BACKUP_TITLE,
                severity=DEFAULT_INCIDENT_SEVERITY,
                attachCaption="OnCall Alert Group",
                attachURL=alert_group.web_link,
            )
        except IncidentAPIException as e:
            # TODO: check for invalid severity?
            logger.error(f"Error creating new incident: {e.msg}")
            # raise (and retry)
            raise
        else:
            _attach_alert_group_to_incident(
                alert_group, incident_data["incidentID"], incident_data["title"], escalation_policy
            )
