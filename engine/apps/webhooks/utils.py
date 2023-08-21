import ipaddress
import json
import re
import socket
from urllib.parse import urlparse

from django.conf import settings

from apps.base.utils import live_settings
from apps.schedules.ical_utils import list_users_to_notify_from_ical
from common.jinja_templater import apply_jinja_template

OUTGOING_WEBHOOK_TIMEOUT = 10


class InvalidWebhookUrl(Exception):
    def __init__(self, message):
        self.message = f"URL - {message}"


class InvalidWebhookTrigger(Exception):
    def __init__(self, message):
        self.message = f"Trigger - {message}"


class InvalidWebhookHeaders(Exception):
    def __init__(self, message):
        self.message = f"Headers - {message}"


class InvalidWebhookData(Exception):
    def __init__(self, message):
        self.message = f"Data - {message}"


def parse_url(url):
    parsed_url = urlparse(url)
    # ensure the url looks like url
    if parsed_url.scheme not in ["http", "https"] or not parsed_url.netloc:
        raise InvalidWebhookUrl("Malformed url")

    if settings.BASE_URL in url:
        raise InvalidWebhookUrl("Potential self-reference")

    if not live_settings.DANGEROUS_WEBHOOKS_ENABLED:
        # Get the ip address of the webhook url and check if it belongs to the private network
        try:
            webhook_url_ip_address = socket.gethostbyname(parsed_url.hostname)
        except socket.gaierror:
            raise InvalidWebhookUrl("Cannot resolve name in url")
        if ipaddress.ip_address(socket.gethostbyname(webhook_url_ip_address)).is_private:
            raise InvalidWebhookUrl("This url is not supported for outgoing webhooks")

    return parsed_url


def apply_jinja_template_for_json(template, payload):
    escaped_payload = escape_payload(payload)
    return apply_jinja_template(template, **escaped_payload)


def escape_payload(payload: dict):
    if isinstance(payload, dict):
        escaped_payload = EscapeDoubleQuotesDict()
        for key in payload.keys():
            escaped_payload[key] = escape_payload(payload[key])
    elif isinstance(payload, list):
        escaped_payload = []
        for value in payload:
            escaped_payload.append(escape_payload(value))
    elif isinstance(payload, str):
        escaped_payload = escape_string(payload)
    else:
        escaped_payload = payload
    return escaped_payload


def escape_string(string: str):
    """
    Escapes string to use in json.loads() method.
    json.dumps is the simples way to escape all special characters in string.
    First and last chars are quotes from json.dumps(), we don't need them, only escaping.
    """
    return json.dumps(string)[1:-1]


class EscapeDoubleQuotesDict(dict):
    """
    Warning: Please, do not use this dict anywhere except CustomButton._escape_alert_payload.
    This custom dict escapes double quotes to produce string which is safe to pass to json.loads()
    It fixes case when CustomButton.build_post_kwargs failing on payloads which contains string with single quote.
    In this case built-in dict's str method will surround value with double quotes.

    For example:

    alert_payload = {
        "text": "Hi, it's alert",
    }
    template = '{"data" : "{{ alert_payload }}"}'
    rendered = '{"data" : "{\'text\': "Hi, it\'s alert"}"}'
    # and json.loads(rendered) will fail due to unescaped double quotes

    # Now with EscapeDoubleQuotesDict.

    alert_payload = EscapeDoubleQuotesDict({
        "text": "Hi, it's alert",
    })
    rendered = '{"data" : "{\'text\': \\"Hi, it\'s alert\\"}"}'
    # and json.loads(rendered) works.
    """

    def __str__(self):
        original_str = super().__str__()
        if '"' in original_str:
            return re.sub('(?<!\\\\)"', '\\\\"', original_str)
        return original_str


def _serialize_event_user(user):
    if not user:
        return None
    return {
        "id": user.public_primary_key,
        "username": user.username,
        "email": user.email,
    }


def _extract_users_from_escalation_snapshot(escalation_snapshot):
    from apps.alerts.models import EscalationPolicy

    users = []
    if escalation_snapshot:
        for policy_snapshot in escalation_snapshot.escalation_policies_snapshots:
            if policy_snapshot.step in [
                EscalationPolicy.STEP_NOTIFY,
                EscalationPolicy.STEP_NOTIFY_IMPORTANT,
                EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
                EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT,
            ]:
                for user in policy_snapshot.notify_to_users_queue:
                    users.append(_serialize_event_user(user))
            elif policy_snapshot.step in [
                EscalationPolicy.STEP_NOTIFY_SCHEDULE,
                EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT,
            ]:
                if policy_snapshot.notify_schedule:
                    for user in list_users_to_notify_from_ical(policy_snapshot.notify_schedule):
                        users.append(_serialize_event_user(user))
    return list({u["id"]: u for u in users if u}.values())


def serialize_event(event, alert_group, user, responses=None):
    from apps.public_api.serializers import IncidentSerializer

    alert_payload = alert_group.alerts.first()
    alert_payload_raw = ""
    if alert_payload:
        alert_payload_raw = alert_payload.raw_request_data

    data = {
        "event": event,
        "user": _serialize_event_user(user),
        "alert_group": IncidentSerializer(alert_group).data,
        "alert_group_id": alert_group.public_primary_key,
        "alert_payload": alert_payload_raw,
        "integration": {
            "id": alert_group.channel.public_primary_key,
            "type": alert_group.channel.integration,
            "name": alert_group.channel.short_name,
            "team": alert_group.channel.team.name if alert_group.channel.team else None,
        },
        "notified_users": [
            _serialize_event_user(user)
            for user in set(notification.author for notification in alert_group.sent_notifications)
        ],
        "users_to_be_notified": _extract_users_from_escalation_snapshot(alert_group.escalation_snapshot),
    }
    if responses:
        data["responses"] = responses

    return data
