import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.metrics_exporter.constants import SERVICE_LABEL
from apps.metrics_exporter.tests.conftest import METRICS_TEST_SERVICE_NAME


@pytest.mark.django_db
def test_alert_group_details(
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_alert_group_label_association,
    settings,
):
    settings.GRAFANA_INCIDENT_STATIC_API_KEY = "test-key"
    headers = {"HTTP_AUTHORIZATION": "test-key"}
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization,
        slack_title_template=None,
        web_title_template="title: {{ payload.field2 }}",
        web_message_template="Something {{ payload.field1 }} + {{ payload.field3 }}",
        web_image_url_template="http://{{ payload.field1 }}.com",
    )
    alert_group = make_alert_group(alert_receive_channel)
    alert_payload = {"field1": "foo", "field2": "bar", "field3": "baz"}
    alert = make_alert(alert_group, alert_payload)

    client = APIClient()

    url = reverse("api-gi:alert-groups-detail", kwargs={"public_primary_key": alert_group.public_primary_key})
    response = client.get(url, format="json", **headers)
    expected = {
        "id": alert_group.public_primary_key,
        "link": alert_group.web_link,
        "status": "new",
        "title": alert_group.long_verbose_name_without_formatting,
        "alerts": [
            {
                "id_oncall": alert.public_primary_key,
                "payload": alert_payload,
            }
        ],
        "labels": [],
        "render_for_web": {
            "title": "title: bar",
            "message": "<p>Something foo + baz</p>",
            "image_url": "http://foo.com",
            "source_link": None,
        },
    }
    assert response.json() == expected
    # enable labels feature flag
    settings.FEATURE_LABELS_ENABLED_FOR_ALL = True
    alert_group_with_labels = make_alert_group(alert_receive_channel)
    alert_with_labels = make_alert(alert_group_with_labels, alert_payload)
    _ = make_alert_group_label_association(
        organization, alert_group_with_labels, key_name=SERVICE_LABEL, value_name=METRICS_TEST_SERVICE_NAME
    )

    url = reverse(
        "api-gi:alert-groups-detail", kwargs={"public_primary_key": alert_group_with_labels.public_primary_key}
    )
    response = client.get(url, format="json", **headers)
    expected = {
        "id": alert_group_with_labels.public_primary_key,
        "link": alert_group_with_labels.web_link,
        "status": "new",
        "title": alert_group_with_labels.long_verbose_name_without_formatting,
        "alerts": [
            {
                "id_oncall": alert_with_labels.public_primary_key,
                "payload": alert_payload,
            }
        ],
        "labels": [
            {
                "key": "service_name",
                "value": "test_service",
            }
        ],
        "render_for_web": {
            "title": "title: bar",
            "message": "<p>Something foo + baz</p>",
            "image_url": "http://foo.com",
            "source_link": None,
        },
    }
    assert response.json() == expected
