---
aliases:
  - add-sentry/
  - /docs/oncall/latest/integrations/available-integrations/configure-Sentry/
canonical: https://grafana.com/docs/oncall/latest/integrations/sentry/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - sentry
title: Sentry
weight: 500
---

# Sentry integration for Grafana OnCall

The Sentry integration for Grafana OnCall handles ticket events sent from Sentry webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin][user-and-team-management] to be able to create integrations in Grafana OnCall.

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

{{% docs/reference %}}
[user-and-team-management]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
[user-and-team-management]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/user-and-team-management"
{{% /docs/reference %}}
