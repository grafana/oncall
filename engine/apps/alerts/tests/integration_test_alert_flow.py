import time
from uuid import uuid4

import pytest

from apps.alerts.models import AlertGroup, AlertReceiveChannel
from apps.integrations.tasks import create_alert

pytest_plugins = ["celery.contrib.pytest"]


@pytest.fixture(scope="session")
def celery_config():
    return {
        "broker_url": "memory://",
    }


@pytest.mark.django_db(transaction=True)  # https://github.com/celery/celery/issues/4511#issuecomment-361659559
def test_create_task(
    celery_app, celery_worker, make_organization, make_alert_receive_channel, make_channel_filter, make_escalation_chain
):
    """
    Tests celery tasks related to the alert lifecycle
    This test is celery specific, see https://docs.celeryq.dev/en/stable/userguide/testing.html
    It uses in memory broker and runs celery worker in separate thread
    Use the following flag to see the tasks logs
    pytest --capture=tee-sys ./apps/alerts/tests/integration_test_alert_flow.py
    """
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_FORMATTED_WEBHOOK
    )
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    default_channel_filter.escalation_chain = make_escalation_chain(organization, name="test")

    TEST_ID = f"unit-test-{uuid4()}"
    create_alert.apply_async(
        [],
        {
            "title": TEST_ID,
            "message": "Smth happened. Oh no!",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/ee/Grumpy_Cat_by_Gage_Skidmore.jpg",
            "link_to_upstream_details": "https://en.wikipedia.org/wiki/Downtime",
            "alert_receive_channel_pk": alert_receive_channel.pk,
            "integration_unique_data": None,
            "raw_request_data": {
                "state": "alerting",
                "title": TEST_ID,
                "message": "Smth happened. Oh no!",
                "alert_uid": "08d6891a-835c-e661-39fa-96b6a9e265520.14148568253291174",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/ee/Grumpy_Cat_by_Gage_Skidmore.jpg",
                "link_to_upstream_details": "https://en.wikipedia.org/wiki/Downtime",
            },
        },
    )
    for _ in range(30):
        alert_groups_count = AlertGroup.all_objects.filter(web_title_cache=TEST_ID).count()
        if alert_groups_count > 0:
            break
        time.sleep(1)
    assert alert_groups_count == 1
