import datetime
import hashlib
import hmac
import json
from base64 import b64encode
from textwrap import dedent
from unittest.mock import ANY, Mock, patch

import pytest
from anymail.inbound import AnymailInboundMessage
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509 import CertificateBuilder, DNSName, NameOID, SubjectAlternativeName
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertReceiveChannel
from apps.email.inbound import InboundEmailWebhookView
from apps.integrations.tasks import create_alert

PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
CERTIFICATE = (
    CertificateBuilder()
    .subject_name(
        x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Test"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Test"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Amazon"),
                x509.NameAttribute(NameOID.COMMON_NAME, "Test"),
            ]
        )
    )
    .issuer_name(
        x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Test"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Test"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Amazon"),
                x509.NameAttribute(NameOID.COMMON_NAME, "Test"),
            ]
        )
    )
    .public_key(PRIVATE_KEY.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.now() - datetime.timedelta(days=1))
    .not_valid_after(datetime.datetime.now() + datetime.timedelta(days=10))
    .add_extension(
        SubjectAlternativeName([DNSName("sns.amazonaws.com")]),
        critical=False,
    )
    .sign(PRIVATE_KEY, hashes.SHA256())
    .public_bytes(serialization.Encoding.PEM)
)
AMAZON_SNS_TOPIC_ARN = "arn:aws:sns:us-east-2:123456789012:test"
SIGNING_CERT_URL = "https://sns.us-east-2.amazonaws.com/SimpleNotificationService-example.pem"


def _sns_inbound_email_payload_and_headers(sender_email, to_email, subject, message):
    content = (
        f"From: Sender Name <{sender_email}>\n"
        f"To: {to_email}\n"
        f"Subject: {subject}\n"
        "Date: Tue, 5 Nov 2024 16:05:39 +0000\n"
        "Message-ID: <example-message-id@mail.example.com>\n\n"
        f"{message}\r\n"
    )

    message = {
        "notificationType": "Received",
        "mail": {
            "timestamp": "2024-11-05T16:05:52.387Z",
            "source": sender_email,
            "messageId": "example-message-id-5678",
            "destination": [to_email],
            "headersTruncated": False,
            "headers": [
                {"name": "Return-Path", "value": f"<{sender_email}>"},
                {
                    "name": "Received",
                    "value": (
                        f"from mail.example.com (mail.example.com [203.0.113.1]) "
                        f"by inbound-smtp.us-east-2.amazonaws.com with SMTP id example-id "
                        f"for {to_email}; Tue, 05 Nov 2024 16:05:52 +0000 (UTC)"
                    ),
                },
                {"name": "X-SES-Spam-Verdict", "value": "PASS"},
                {"name": "X-SES-Virus-Verdict", "value": "PASS"},
                {
                    "name": "Received-SPF",
                    "value": (
                        "pass (spfCheck: domain of example.com designates 203.0.113.1 as permitted sender) "
                        f"client-ip=203.0.113.1; envelope-from={sender_email}; helo=mail.example.com;"
                    ),
                },
                {
                    "name": "Authentication-Results",
                    "value": (
                        "amazonses.com; spf=pass (spfCheck: domain of example.com designates 203.0.113.1 as permitted sender) "
                        f"client-ip=203.0.113.1; envelope-from={sender_email}; helo=mail.example.com; "
                        "dkim=pass header.i=@example.com; dmarc=pass header.from=example.com;"
                    ),
                },
                {"name": "X-SES-RECEIPT", "value": "example-receipt-data"},
                {"name": "X-SES-DKIM-SIGNATURE", "value": "example-dkim-signature"},
                {
                    "name": "Received",
                    "value": (
                        f"by mail.example.com with SMTP id example-id for <{to_email}>; "
                        "Tue, 05 Nov 2024 08:05:52 -0800 (PST)"
                    ),
                },
                {
                    "name": "DKIM-Signature",
                    "value": (
                        "v=1; a=rsa-sha256; c=relaxed/relaxed; d=example.com; s=default; t=1234567890; "
                        "bh=examplehash; h=From:To:Subject:Date:Message-ID; b=example-signature"
                    ),
                },
                {"name": "X-Google-DKIM-Signature", "value": "example-google-dkim-signature"},
                {"name": "X-Gm-Message-State", "value": "example-message-state"},
                {"name": "X-Google-Smtp-Source", "value": "example-smtp-source"},
                {
                    "name": "X-Received",
                    "value": "by 2002:a17:example with SMTP id example-id; Tue, 05 Nov 2024 08:05:50 -0800 (PST)",
                },
                {"name": "MIME-Version", "value": "1.0"},
                {"name": "From", "value": f"Sender Name <{sender_email}>"},
                {"name": "Date", "value": "Tue, 5 Nov 2024 16:05:39 +0000"},
                {"name": "Message-ID", "value": "<example-message-id@mail.example.com>"},
                {"name": "Subject", "value": subject},
                {"name": "To", "value": to_email},
                {
                    "name": "Content-Type",
                    "value": 'multipart/alternative; boundary="00000000000036b9f706262c9312"',
                },
            ],
            "commonHeaders": {
                "returnPath": sender_email,
                "from": [f"Sender Name <{sender_email}>"],
                "date": "Tue, 5 Nov 2024 16:05:39 +0000",
                "to": [to_email],
                "messageId": "<example-message-id@mail.example.com>",
                "subject": subject,
            },
        },
        "receipt": {
            "timestamp": "2024-11-05T16:05:52.387Z",
            "processingTimeMillis": 638,
            "recipients": [to_email],
            "spamVerdict": {"status": "PASS"},
            "virusVerdict": {"status": "PASS"},
            "spfVerdict": {"status": "PASS"},
            "dkimVerdict": {"status": "PASS"},
            "dmarcVerdict": {"status": "PASS"},
            "action": {
                "type": "SNS",
                "topicArn": "arn:aws:sns:us-east-2:123456789012:test",
                "encoding": "BASE64",
            },
        },
        "content": b64encode(content.encode()).decode(),
    }

    payload = {
        "Type": "Notification",
        "MessageId": "example-message-id-1234",
        "TopicArn": AMAZON_SNS_TOPIC_ARN,
        "Subject": "Amazon SES Email Receipt Notification",
        "Message": json.dumps(message),
        "Timestamp": "2024-11-05T16:05:53.041Z",
        "SignatureVersion": "1",
        "SigningCertURL": SIGNING_CERT_URL,
        "UnsubscribeURL": (
            "https://sns.us-east-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn="
            "arn:aws:sns:us-east-2:123456789012:test:example-subscription-id"
        ),
    }
    # Sign the payload
    canonical_message = "".join(
        f"{key}\n{payload[key]}\n" for key in ("Message", "MessageId", "Subject", "Timestamp", "TopicArn", "Type")
    )
    signature = PRIVATE_KEY.sign(
        canonical_message.encode(),
        padding.PKCS1v15(),
        hashes.SHA1(),
    )
    payload["Signature"] = b64encode(signature).decode()

    headers = {
        "X-Amz-Sns-Message-Type": "Notification",
        "X-Amz-Sns-Message-Id": "example-message-id-1234",
    }
    return payload, headers


def _mailgun_inbound_email_payload(sender_email, to_email, subject, message):
    timestamp, token = "1731341416", "example-token"
    signature = hmac.new(
        key=settings.INBOUND_EMAIL_WEBHOOK_SECRET.encode("ascii"),
        msg="{}{}".format(timestamp, token).encode("ascii"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    return {
        "Content-Type": 'multipart/alternative; boundary="000000000000267130626a556e5"',
        "Date": "Mon, 11 Nov 2024 16:10:03 +0000",
        "Dkim-Signature": (
            "v=1; a=rsa-sha256; c=relaxed/relaxed; d=example.com; s=default; "
            "t=1731341415; x=1731946215; darn=example.com; "
            "h=to:subject:message-id:date:from:mime-version:from:to:cc:subject "
            ":date:message-id:reply-to; bh=examplebh; b=exampleb"
        ),
        "From": f"Sender Name <{sender_email}>",
        "Message-Id": "<example-message-id@mail.example.com>",
        "Mime-Version": "1.0",
        "Received": (
            f"by mail.example.com with SMTP id example-id for <{to_email}>; " "Mon, 11 Nov 2024 08:10:15 -0800 (PST)"
        ),
        "Subject": subject,
        "To": to_email,
        "X-Envelope-From": sender_email,
        "X-Gm-Message-State": "example-message-state",
        "X-Google-Dkim-Signature": (
            "v=1; a=rsa-sha256; c=relaxed/relaxed; d=1e100.net; s=20230601; "
            "t=1731341415; x=1731946215; "
            "h=to:subject:message-id:date:from:mime-version:x-gm-message-state "
            ":from:to:cc:subject:date:message-id:reply-to; bh=examplebh; b=exampleb"
        ),
        "X-Google-Smtp-Source": "example-smtp-source",
        "X-Mailgun-Incoming": "Yes",
        "X-Received": "by 2002:a17:example with SMTP id example-id; Mon, 11 Nov 2024 08:10:14 -0800 (PST)",
        "body-html": f'<div dir="ltr">{message}<br></div>\r\n',
        "body-plain": f"{message}\r\n",
        "from": f"Sender Name <{sender_email}>",
        "message-headers": json.dumps(
            [
                ["X-Mailgun-Incoming", "Yes"],
                ["X-Envelope-From", sender_email],
                [
                    "Received",
                    (
                        "from mail.example.com (mail.example.com [203.0.113.1]) "
                        "by example.com with SMTP id example-id; "
                        "Mon, 11 Nov 2024 16:10:15 GMT"
                    ),
                ],
                [
                    "Received",
                    (
                        f"by mail.example.com with SMTP id example-id for <{to_email}>; "
                        "Mon, 11 Nov 2024 08:10:15 -0800 (PST)"
                    ),
                ],
                [
                    "Dkim-Signature",
                    (
                        "v=1; a=rsa-sha256; c=relaxed/relaxed; d=example.com; s=default; "
                        "t=1731341415; x=1731946215; darn=example.com; "
                        "h=to:subject:message-id:date:from:mime-version:from:to:cc:subject "
                        ":date:message-id:reply-to; bh=examplebh; b=exampleb"
                    ),
                ],
                [
                    "X-Google-Dkim-Signature",
                    (
                        "v=1; a=rsa-sha256; c=relaxed/relaxed; d=1e100.net; s=20230601; "
                        "t=1731341415; x=1731946215; "
                        "h=to:subject:message-id:date:from:mime-version:x-gm-message-state "
                        ":from:to:cc:subject:date:message-id:reply-to; bh=examplebh; b=exampleb"
                    ),
                ],
                ["X-Gm-Message-State", "example-message-state"],
                ["X-Google-Smtp-Source", "example-smtp-source"],
                [
                    "X-Received",
                    "by 2002:a17:example with SMTP id example-id; Mon, 11 Nov 2024 08:10:14 -0800 (PST)",
                ],
                ["Mime-Version", "1.0"],
                ["From", f"Sender Name <{sender_email}>"],
                ["Date", "Mon, 11 Nov 2024 16:10:03 +0000"],
                ["Message-Id", "<example-message-id@mail.example.com>"],
                ["Subject", subject],
                ["To", to_email],
                [
                    "Content-Type",
                    'multipart/alternative; boundary="000000000000267130626a556e5"',
                ],
            ]
        ),
        "recipient": to_email,
        "sender": sender_email,
        "signature": signature,
        "stripped-html": f'<div dir="ltr">{message}<br></div>\n',
        "stripped-text": f"{message}\n",
        "subject": subject,
        "timestamp": timestamp,
        "token": token,
    }


@pytest.mark.parametrize(
    "recipients,expected",
    [
        ("{token}@example.com", status.HTTP_200_OK),
        ("{token}@example.com, another@example.com", status.HTTP_200_OK),
        ("{token}@example.com, another@example.com", status.HTTP_200_OK),
        ("{token}@other.com, {token}@example.com", status.HTTP_400_BAD_REQUEST),
    ],
)
@pytest.mark.django_db
@pytest.mark.filterwarnings("ignore:::anymail.*")  # ignore missing WEBHOOK_SECRET in amazon ses test setup
def test_amazon_ses_provider_load(
    settings, make_organization_and_user_with_token, make_alert_receive_channel, recipients, expected
):
    settings.INBOUND_EMAIL_ESP = "amazon_ses"
    settings.INBOUND_EMAIL_DOMAIN = "example.com"

    dummy_channel_token = "dummy-channel-token"

    organization, _, token = make_organization_and_user_with_token()
    _ = make_alert_receive_channel(organization, token=dummy_channel_token)

    recipients = recipients.format(token=dummy_channel_token)
    mime = f"""From: sender@example.com
    Subject: Dummy email message
    To: {recipients}
    Content-Type: text/plain

    Hello!
    """

    message = {
        "notificationType": "Received",
        "receipt": {"action": {"type": "SNS"}, "recipients": recipients.split(",")},
        "content": mime,
    }

    dummy_sns_message_id = "22b80b92-fdea-4c2c-8f9d-bdfb0c7bf324"
    dummy_sns_payload = {
        "Type": "Notification",
        "MessageId": dummy_sns_message_id,
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:MyTopic",
        "Subject": "My First Message",
        "Message": json.dumps(message),
    }

    client = APIClient()

    response = client.post(
        reverse("integrations:inbound_email_webhook"),
        data=json.dumps(dummy_sns_payload),
        content_type="application/json",
        HTTP_AUTHORIZATION=token,
        HTTP_X_AMZ_SNS_MESSAGE_TYPE="Notification",
        HTTP_X_AMZ_SNS_MESSAGE_ID=dummy_sns_message_id,
    )

    assert response.status_code == expected


@pytest.mark.parametrize(
    "recipients,expected",
    [
        ("{token}@example.com", status.HTTP_200_OK),
        ("{token}@example.com, another@example.com", status.HTTP_200_OK),
        ("{token}@example.com, another@example.com", status.HTTP_200_OK),
        ("{token}@other.com, {token}@example.com", status.HTTP_200_OK),
        ("{token}@other.com, {token}@another.com", status.HTTP_400_BAD_REQUEST),
    ],
)
@pytest.mark.django_db
def test_mailgun_provider_load(
    settings, make_organization_and_user_with_token, make_alert_receive_channel, recipients, expected
):
    settings.INBOUND_EMAIL_ESP = "mailgun"
    settings.INBOUND_EMAIL_DOMAIN = "example.com"
    settings.INBOUND_EMAIL_WEBHOOK_SECRET = "secret"

    dummy_channel_token = "dummy-channel-token"

    organization, _, token = make_organization_and_user_with_token()
    _ = make_alert_receive_channel(organization, token=dummy_channel_token)

    recipients = recipients.format(token=dummy_channel_token)
    raw_event = {
        "token": "06c96bafc3f42a66b9edd546347a2fe18dc23461fe80dc52f0",
        "timestamp": "1461261330",
        "signature": "dbb05e62be402448b36ffb81f6abfb888273c95617aa077b4da355b25bab3670",
        "recipient": "{recipients}".format(recipients=recipients),
        "sender": "envelope-from@example.org",
        "body-mime": dedent(
            """\
        From: sender@example.com
        Subject: Dummy email message
        To: {recipients}
        Content-Type: text/plain

        Hello!
        --94eb2c05e174adb140055b6339c5--
        """.format(
                recipients=recipients
            )
        ),
    }

    client = APIClient()
    response = client.post(
        reverse("integrations:inbound_email_webhook"),
        data=raw_event,
        HTTP_AUTHORIZATION=token,
    )

    assert response.status_code == expected


@pytest.mark.parametrize(
    "sender_value,expected_result",
    [
        ("'Alex Smith' <test@example.com>", "test@example.com"),
        # double quotes required when including special characters
        ("\"'Alex Smith' via [TEST] mail\" <test@example.com>", "test@example.com"),
        # missing double quotes
        ("'Alex Smith' via [TEST] mail <test@example.com>", "\"'Alex Smith' via\""),
    ],
)
def test_get_sender_from_email_message(sender_value, expected_result):
    email = AnymailInboundMessage()
    email["From"] = sender_value
    view = InboundEmailWebhookView()
    result = view.get_sender_from_email_message(email)
    assert result == expected_result


@patch.object(create_alert, "delay")
@pytest.mark.django_db
def test_amazon_ses_pass(create_alert_mock, settings, make_organization, make_alert_receive_channel):
    settings.INBOUND_EMAIL_ESP = "amazon_ses,mailgun"
    settings.INBOUND_EMAIL_DOMAIN = "inbound.example.com"
    settings.INBOUND_EMAIL_WEBHOOK_SECRET = "secret"

    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_INBOUND_EMAIL,
        token="test-token",
    )

    sender_email = "sender@example.com"
    to_email = "test-token@inbound.example.com"
    subject = "Test email"
    message = "This is a test email message body."
    sns_payload, sns_headers = _sns_inbound_email_payload_and_headers(
        sender_email=sender_email,
        to_email=to_email,
        subject=subject,
        message=message,
    )

    client = APIClient()
    response = client.post(
        reverse("integrations:inbound_email_webhook"),
        data=sns_payload,
        headers=sns_headers,
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    create_alert_mock.assert_called_once_with(
        title=subject,
        message=message,
        alert_receive_channel_pk=alert_receive_channel.pk,
        image_url=None,
        link_to_upstream_details=None,
        integration_unique_data=None,
        raw_request_data={
            "subject": subject,
            "message": message,
            "sender": sender_email,
        },
        received_at=ANY,
    )


@patch("requests.get", return_value=Mock(content=CERTIFICATE))
@patch.object(create_alert, "delay")
@pytest.mark.django_db
def test_amazon_ses_validated_pass(
    mock_create_alert, mock_requests_get, settings, make_organization, make_alert_receive_channel
):
    settings.INBOUND_EMAIL_ESP = "amazon_ses_validated,mailgun"
    settings.INBOUND_EMAIL_DOMAIN = "inbound.example.com"
    settings.INBOUND_EMAIL_WEBHOOK_SECRET = "secret"
    settings.INBOUND_EMAIL_AMAZON_SNS_TOPIC_ARN = AMAZON_SNS_TOPIC_ARN

    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_INBOUND_EMAIL,
        token="test-token",
    )

    sender_email = "sender@example.com"
    to_email = "test-token@inbound.example.com"
    subject = "Test email"
    message = "This is a test email message body."
    sns_payload, sns_headers = _sns_inbound_email_payload_and_headers(
        sender_email=sender_email,
        to_email=to_email,
        subject=subject,
        message=message,
    )

    client = APIClient()
    response = client.post(
        reverse("integrations:inbound_email_webhook"),
        data=sns_payload,
        headers=sns_headers,
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    mock_create_alert.assert_called_once_with(
        title=subject,
        message=message,
        alert_receive_channel_pk=alert_receive_channel.pk,
        image_url=None,
        link_to_upstream_details=None,
        integration_unique_data=None,
        raw_request_data={
            "subject": subject,
            "message": message,
            "sender": sender_email,
        },
        received_at=ANY,
    )

    mock_requests_get.assert_called_once_with(SIGNING_CERT_URL, timeout=5)


@patch.object(create_alert, "delay")
@pytest.mark.django_db
def test_mailgun_pass(create_alert_mock, settings, make_organization, make_alert_receive_channel):
    settings.INBOUND_EMAIL_ESP = "amazon_ses,mailgun"
    settings.INBOUND_EMAIL_DOMAIN = "inbound.example.com"
    settings.INBOUND_EMAIL_WEBHOOK_SECRET = "secret"

    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_INBOUND_EMAIL,
        token="test-token",
    )

    sender_email = "sender@example.com"
    to_email = "test-token@inbound.example.com"
    subject = "Test email"
    message = "This is a test email message body."

    mailgun_payload = _mailgun_inbound_email_payload(
        sender_email=sender_email,
        to_email=to_email,
        subject=subject,
        message=message,
    )

    client = APIClient()
    response = client.post(
        reverse("integrations:inbound_email_webhook"),
        data=mailgun_payload,
        format="multipart",
    )

    assert response.status_code == status.HTTP_200_OK
    create_alert_mock.assert_called_once_with(
        title=subject,
        message=message,
        alert_receive_channel_pk=alert_receive_channel.pk,
        image_url=None,
        link_to_upstream_details=None,
        integration_unique_data=None,
        raw_request_data={
            "subject": subject,
            "message": message,
            "sender": sender_email,
        },
        received_at=ANY,
    )


@pytest.mark.django_db
def test_multiple_esps_fail(settings):
    settings.INBOUND_EMAIL_ESP = "amazon_ses,mailgun"
    settings.INBOUND_EMAIL_DOMAIN = "example.com"
    settings.INBOUND_EMAIL_WEBHOOK_SECRET = "secret"

    client = APIClient()
    response = client.post(reverse("integrations:inbound_email_webhook"), data={})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
