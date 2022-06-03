import pytest

from apps.alerts.models import Alert, AlertReceiveChannel
from apps.integrations.tasks import create_alertmanager_alerts


@pytest.mark.django_db
def test_create_alertmanager_alert_deleted_task_no_alert_no_retry(
    make_organization,
    make_alert_receive_channel,
):
    organization = make_organization()
    integration = make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_WEBHOOK)
    integration.delete()

    create_alertmanager_alerts(integration.pk, {})

    assert Alert.objects.count() == 0


@pytest.mark.django_db
def test_create_alertmanager_alert_maintanance_task_no_alert_no_retry(
    make_organization,
    make_alert_receive_channel,
):
    organization = make_organization()
    integration = make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_MAINTENANCE)

    create_alertmanager_alerts(integration.pk, {})

    assert Alert.objects.count() == 0
