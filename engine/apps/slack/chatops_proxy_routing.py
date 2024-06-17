import json
import typing


# ProxyMeta is a data injected into various Slack payloads to route them to the correct cluster via Chatops-Proxy
# Short keys are used to satisfy slack limit for 155 chars in values
class ProxyMeta(typing.TypedDict):
    s: str  # s is a service name
    tid: str  # tid is a tenant_id


def make_value(data: dict, organization) -> str:
    # Slack block elements allow to pass value as string only (max 2000 chars)
    return json.dumps({**data, "s": "oncall", "tid": str(organization.uuid)})


def make_private_metadata(data: dict, organization) -> str:
    return json.dumps({**data, "s": "oncall", "tid": str(organization.uuid)})
