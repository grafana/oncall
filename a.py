from common.oncall_gateway.oncall_gateway_client import OnCallGatewayAPIClient
from apps.user_management.models import Organization
from django.conf import settings
import requests

client = OnCallGatewayAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
orgs_with_slack_id = Organization.objects.filter(slack_team_identity__isnull=False).select_related("slack_team_identity")
for idx, o in enumerate(orgs_with_slack_id):
    try:
        print(f"Processing {o.stack_slug} oncall_uuid={str(o.uuid)} stack_id={o.stack_id} org_id={o.org_id} slack_id={o.slack_team_identity.slack_id} is_moved={o.is_moved}")
        client.post_slack_connector(str(o.uuid), o.slack_team_identity.slack_id, settings.ONCALL_BACKEND_REGION)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            if "slack connected to another backend" in str(e):
                print(f"Conflict for {o.stack_slug} oncall_uuid={str(o.uuid)} stack_id={o.stack_id} org_id={o.org_id} slack_id={o.slack_team_identity.slack_id} is_moved={o.is_moved}")
        else:
            print(f"UNEXPECTED {e}")
