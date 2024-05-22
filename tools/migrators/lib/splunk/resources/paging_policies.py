import typing

from lib.oncall.api_client import OnCallAPIClient
from lib.splunk.config import SPLUNK_TO_ONCALL_CONTACT_METHOD_MAP
from lib.splunk.types import SplunkUserPagingPolicy, SplunkUserWithPagingPolicies
from lib.utils import transform_wait_delay


def migrate_paging_policies(user: SplunkUserWithPagingPolicies) -> None:
    paging_policies = user["pagingPolicies"]
    oncall_rules = transform_paging_policies(paging_policies, user["oncall_user"]["id"])

    for rule in oncall_rules:
        OnCallAPIClient.create("personal_notification_rules", rule)

    if oncall_rules:
        # delete old notification rules if any new rules were created
        for rule in user["oncall_user"]["notification_rules"]:
            OnCallAPIClient.delete("personal_notification_rules/{}".format(rule["id"]))


def transform_paging_policies(
    paging_policies: typing.List[SplunkUserPagingPolicy], user_id: str
) -> typing.List[SplunkUserPagingPolicy]:
    """
    Transform Splunk user paging policies to Grafana OnCall personal notification rules.
    """
    paging_policies = sorted(paging_policies, key=lambda rule: rule["order"])
    oncall_notification_rules = []

    for idx, paging_policy in enumerate(paging_policies):
        # don't add a delay at the end
        if idx == len(paging_policies) - 1:
            delay = None
        else:
            delay = paging_policy["timeout"]

        oncall_notification_rules += transform_paging_policy(
            paging_policy, delay, user_id
        )
    return oncall_notification_rules


def transform_paging_policy(
    paging_policy: SplunkUserPagingPolicy, delay: typing.Optional[int], user_id: str
) -> list[dict]:
    oncall_type = SPLUNK_TO_ONCALL_CONTACT_METHOD_MAP[paging_policy["contactType"]]

    notify_rule = {"user_id": user_id, "type": oncall_type, "important": False}

    if not delay:
        return [notify_rule]

    wait_rule = {
        "user_id": user_id,
        "type": "wait",
        "duration": transform_wait_delay(delay),
        "important": False,
    }
    return [notify_rule, wait_rule]
