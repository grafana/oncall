---
title: Sentry integration for Grafana OnCall
menuTitle: Sentry
description: Sentry integration reference material for Grafana OnCall.
weight: 0
keywords:
  - OnCall
  - Integrations
  - Alerts
  - Sentry
  - Notifications
labels:
  products:
    - cloud
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/references/sentry
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/sentry
  - /docs/grafana-cloud/alerting-and-irm/oncall/integrations/sentry
  - add-sentry/
  - ../integrations/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/sentry
refs:
  user-and-team-management:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/user-and-team-management/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/user-and-team-management/
---

# Sentry integration for Grafana OnCall

{{< admonition type="note" >}}
This integration is available exclusively on Grafana Cloud.
{{< /admonition >}}

The Sentry integration for Grafana OnCall handles ticket events sent from Sentry webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

## Configuring Grafana OnCall to Receive Alerts from Sentry

1. In the **Integrations** tab, click **+ New integration**.
2. Select **Sentry** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.

## Configuring Sentry to Send Alerts to Grafana OnCall

To send a webhook alert from Sentry, you can follow these steps:

1. Log in to your Sentry account.

2. Navigate to your project's settings.

3. Click on "Alerts" in the sidebar menu.

4. Click on "New Alert Rule" to create a new alert rule.

5. Configure the conditions for the alert rule based on your requirements. For example, you can set conditions based on issue
level, event frequency, or specific tags.

6. In the "Actions" section, select "Webhook" as the action type.

7. Provide the necessary details for the webhook:

   - **URL**: **OnCall Integration URL**
   - **Method**: POST
   - **Payload**: Define the payload structure and content that you want to send to the webhook endpoint. You can use Sentry's
   dynamic variables to include relevant information in the payload.

8. Save the alert rule.

Once the alert conditions are met, Sentry will trigger the webhook action and send a request to the Grafana OnCall.
