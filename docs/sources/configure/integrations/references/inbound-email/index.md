---
title: Inbound email integration for Grafana OnCall
menuTitle: Inbound email
description: Inbound email integration reference material for Grafana OnCall.
weight: 0
keywords:
  - OnCall
  - Integrations
  - Alerts
  - Inbound email
  - Email
  - Notifications
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/references/inbound-email
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/inbound-email
  - /docs/grafana-cloud/alerting-and-irm/oncall/integrations/inbound-email
  - ../integrations/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/inbound-email
refs:
  inbound-email-setup:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/set-up/open-source/#inbound-email-setup
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/set-up/open-source/#inbound-email-setup
  jinja2-templating:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating/
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
 This behaviour can be modified via [custom templates](ref:jinja2-templating).

Alerts from Inbound Email integration have the following payload:

```json
{
   "subject": "<your_email_subject>",
   "message": "<your_email_message>",
   "sender": "<your_email_sender_address>"
}
```
