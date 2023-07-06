---
aliases:
  - inbound-email/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-inbound-email/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - Email
title: Inbound Email
weight: 500
---

# Inbound Email integration for Grafana OnCall

Inbound Email integration will consume emails from dedicated email address and make alert groups from them.

## Configure Inbound Email integration for Grafana OnCall

You must have an Admin role to create integrations in Grafana OnCall.

1. In the **Integrations** tab, click **+ New integration to receive alerts**.
2. Select **Inbound Email** from the list of available integrations.
3. Get your dedicated email address in the **Integration email** section and use it to send your emails.

## Grouping and auto-resolve

Alert groups will be grouped by email subject and auto-resolved if the email message text equals "OK".
 This behaviour can be modified via [custom templates][jinja2-templating].

Alerts from Inbound Email integration have the following payload:

```json
{
   "subject": "<your_email_subject>",
   "message": "<your_email_message>",
   "sender": "<your_email_sender_address>"
}
```

{{% docs/reference %}}
[jinja2-templating]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/jinja2-templating"
[jinja2-templating]: "/docs/grafana-cloud/ -> /docs/oncall/<ONCALL VERSION>/jinja2-templating"
{{% /docs/reference %}}
