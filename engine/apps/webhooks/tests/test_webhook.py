from unittest.mock import call, patch

import pytest
from requests.auth import HTTPBasicAuth

from apps.webhooks.models import Webhook
from apps.webhooks.utils import (
    OUTGOING_WEBHOOK_TIMEOUT,
    InvalidWebhookData,
    InvalidWebhookHeaders,
    InvalidWebhookTrigger,
    InvalidWebhookUrl,
)


@pytest.mark.django_db
def test_soft_delete(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(organization=organization)
    assert webhook.deleted_at is None
    webhook.delete()

    webhook.refresh_from_db()
    assert webhook.deleted_at is not None

    assert Webhook.objects.all().count() == 0
    assert Webhook.objects_with_deleted.all().count() == 1


@pytest.mark.django_db
def test_hard_delete(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(organization=organization)
    assert webhook.pk is not None
    webhook.hard_delete()

    assert webhook.pk is None
    assert Webhook.objects.all().count() == 0
    assert Webhook.objects_with_deleted.all().count() == 0


@pytest.mark.django_db
def test_build_request_kwargs_none(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(organization=organization)
    request_kwargs = webhook.build_request_kwargs({})

    assert request_kwargs == {"headers": {}, "json": {}}


@pytest.mark.django_db
def test_build_request_kwargs_http_auth(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(organization=organization, username="foo", password="bar")
    request_kwargs = webhook.build_request_kwargs({})

    expected = HTTPBasicAuth("foo", "bar")
    assert request_kwargs == {"headers": {}, "json": {}, "auth": expected}


@pytest.mark.django_db
def test_build_request_kwargs_headers(make_organization, make_custom_webhook):
    organization = make_organization()

    # non json
    headers = "non-json"
    webhook = make_custom_webhook(organization=organization, headers=headers)
    with pytest.raises(InvalidWebhookHeaders):
        webhook.build_request_kwargs({})

    # template error
    headers = "{{{foo|invalid}}}"
    webhook = make_custom_webhook(organization=organization, headers=headers)
    with pytest.raises(InvalidWebhookHeaders):
        webhook.build_request_kwargs({})

    # ok (using event data)
    headers = '{"{{foo}}": "bar"}'
    webhook = make_custom_webhook(organization=organization, headers=headers)
    assert webhook.forward_all
    request_kwargs = webhook.build_request_kwargs({"foo": "bar"})
    assert request_kwargs == {"headers": {"bar": "bar"}, "json": {"foo": "bar"}}


@pytest.mark.django_db
def test_build_request_kwargs_authorization_header(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(organization=organization, authorization_header="some-token")
    request_kwargs = webhook.build_request_kwargs({})

    assert request_kwargs == {"headers": {"Authorization": "some-token"}, "json": {}}


@pytest.mark.django_db
def test_build_request_kwargs_http_get(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(organization=organization, http_method="GET")
    request_kwargs = webhook.build_request_kwargs({})

    assert request_kwargs == {"headers": {}}


@pytest.mark.django_db
def test_build_request_kwargs_custom_data(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(organization=organization, data="{{foo}}", forward_all=False)
    request_kwargs = webhook.build_request_kwargs({"foo": "bar", "something": "else"})

    assert request_kwargs == {"headers": {}, "data": "bar"}


@pytest.mark.django_db
def test_build_request_kwargs_is_legacy_custom_data(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(
        organization=organization,
        data="{{alert_payload.message}}",
        forward_all=False,
        is_legacy=True,
    )
    event_data = {"alert_group_id": "bar", "alert_payload": {"message": "the-message"}}
    request_kwargs = webhook.build_request_kwargs(event_data)

    assert request_kwargs == {"headers": {}, "data": "the-message"}


@pytest.mark.django_db
def test_build_request_kwargs_is_legacy_forward_all(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(
        organization=organization,
        forward_all=True,
        is_legacy=True,
    )
    event_data = {"alert_group_id": "bar", "alert_payload": {"message": "the-message"}}
    request_kwargs = webhook.build_request_kwargs(event_data)

    assert request_kwargs == {"headers": {}, "json": event_data["alert_payload"]}


@pytest.mark.django_db
def test_build_request_kwargs_custom_data_error(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(organization=organization, data="{{foo|invalid}}", forward_all=False)

    # raise
    with pytest.raises(InvalidWebhookData):
        webhook.build_request_kwargs({"foo": "bar", "something": "else"}, raise_data_errors=True)

    # do not raise
    request_kwargs = webhook.build_request_kwargs({"foo": "bar", "something": "else"})
    assert request_kwargs == {"headers": {}, "json": {"error": "Template Error: No filter named 'invalid'."}}


@pytest.mark.django_db
def test_build_url_invalid_template(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(organization=organization, url="{{foo|invalid}}")

    with pytest.raises(InvalidWebhookUrl):
        webhook.build_url({})


@pytest.mark.django_db
def test_build_url_invalid_url(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(organization=organization, url="{{foo}}")

    with pytest.raises(InvalidWebhookUrl):
        webhook.build_url({"foo": "invalid-url"})


@pytest.mark.django_db
def test_build_url_private_raises(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(organization=organization, url="{{foo}}")

    with pytest.raises(InvalidWebhookUrl):
        with patch("apps.webhooks.utils.socket.gethostbyname") as mock_gethostbyname:
            mock_gethostbyname.return_value = "127.0.0.1"
            webhook.build_url({"foo": "http://oncall.url"})


@pytest.mark.django_db
def test_build_url_ok(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(organization=organization, url="{{foo}}")

    with patch("apps.webhooks.utils.socket.gethostbyname") as mock_gethostbyname:
        mock_gethostbyname.return_value = "8.8.8.8"
        url = webhook.build_url({"foo": "http://oncall.url"})

    assert url == "http://oncall.url"


@pytest.mark.django_db
def test_check_trigger_empty(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(organization=organization)

    ok, result = webhook.check_trigger({})
    assert ok
    assert result == ""


@pytest.mark.django_db
def test_check_trigger_template_error(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(organization=organization, trigger_template="{{foo|invalid}}")

    with pytest.raises(InvalidWebhookTrigger):
        webhook.check_trigger({"foo": "bar"})


@pytest.mark.django_db
def test_check_trigger_template_ok(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(organization=organization, trigger_template="{{ foo }}")

    ok, result = webhook.check_trigger({"foo": "true"})
    assert ok
    assert result == "true"

    ok, result = webhook.check_trigger({"foo": "bar"})
    assert not ok
    assert result == "bar"


@pytest.mark.django_db
def test_make_request(make_organization, make_custom_webhook):
    organization = make_organization()

    with patch("apps.webhooks.models.webhook.requests") as mock_requests:
        for method in ("GET", "POST", "PUT", "DELETE", "OPTIONS"):
            webhook = make_custom_webhook(organization=organization, http_method=method)
            webhook.make_request("url", {"foo": "bar"})
            expected_call = getattr(mock_requests, method.lower())
            assert expected_call.called
            assert expected_call.call_args == call("url", timeout=OUTGOING_WEBHOOK_TIMEOUT, foo="bar")

    # invalid
    with pytest.raises(Exception):
        webhook = make_custom_webhook(organization=organization, http_method="NOT")
        webhook.make_request("url", {"foo": "bar"})


@pytest.mark.django_db
def test_escaping_payload_with_double_quotes(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(
        organization=organization,
        data='{\n "text" : "{{ alert_payload.text }}"\n}',
        forward_all=False,
    )

    payload = {
        "alert_payload": {
            "text": '"Hello world"',
        }
    }
    request_kwargs = webhook.build_request_kwargs(payload)
    assert request_kwargs == {"headers": {}, "json": {"text": '"Hello world"'}}


@pytest.mark.django_db
def test_escaping_payload_with_single_quote_in_string(make_organization, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(
        organization=organization,
        data='{"data" : "{{ alert_payload }}"}',
        forward_all=False,
    )

    payload = {
        "alert_payload": {
            "text": "Hi, it's alert",
        }
    }
    request_kwargs = webhook.build_request_kwargs(payload)
    assert request_kwargs == {"headers": {}, "json": {"data": "{'text': \"Hi, it's alert\"}"}}
