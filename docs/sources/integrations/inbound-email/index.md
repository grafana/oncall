---
aliases:
  - inbound-email/
canonical: https://grafana.com/docs/oncall/latest/integrations/inbound-email/
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

## Configure required environment variables

Refer to [Inbound Email Setup] for details.

## Configure Inbound Email integration for Grafana OnCall

You must have an Admin role to create integrations in Grafana OnCall.

1. In the **Integrations** tab, click **+ New integration to receive alerts**.
2. Select **Inbound Email** from the list of available integrations.
3. Get your dedicated email address in the **Integration email** section and use it to send your emails.

## Grouping and auto-resolve

Alert groups will be grouped by email subject and auto-resolved if the email message text equals "OK".
 This behaviour can be modified via an integration's [behavioral templates][].

Alerts from Inbound Email integration have the following payload:

```json
{
   "subject": "<your_email_subject>",
   "message": "<your_email_message>",
   "sender": "<your_email_sender_address>"
}
```

{{% docs/reference %}}
[behavioral templates]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/integrations#behavioral-templates"
[behavioral templates]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating"

[Inbound Email Setup]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/set-up/open-source#inbound-email-setup"
[Inbound Email Setup]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/set-up/open-source#inbound-email-setup"
{{% /docs/reference %}}
