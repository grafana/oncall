from unittest.mock import call, patch

import pytest

from apps.alerts.tasks import custom_webhook_result


@pytest.mark.django_db
def test_custom_webhook_result_executes_webhook():
    webhook_id = 42
    alert_group_id = 13
    escalation_policy_id = 11

    with patch("apps.webhooks.tasks.trigger_webhook.execute_webhook.apply_async") as mock_execute:
        custom_webhook_result(webhook_id, alert_group_id, escalation_policy_id)

    assert mock_execute.call_args == call((webhook_id, alert_group_id, None, escalation_policy_id))
