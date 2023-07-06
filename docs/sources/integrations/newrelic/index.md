---
aliases:
  - add-newrelic/
  - /docs/oncall/latest/integrations/available-integrations/configure-newrelic/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-newrelic/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - newrelic
title: New Relic
weight: 500
---

# New Relic integration for Grafana OnCall

The New Relic integration for Grafana OnCall handles ticket events sent from New Relic webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin][user-and-team-management] to be able to create integrations in Grafana OnCall.

## Configuring Grafana OnCall to Receive Alerts from New Relic

1. In the **Integrations** tab, click **+ New integration**.
2. Select **New Relic** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.

## Configuring New Relic to Send Alerts to Grafana OnCall

1. Go to "Alerts".
2. Go to "Notification Channels".
3. Create "Webhook" notification channel.
4. Set the following URL: **OnCall Integration URL**
5. Check "Payload type" is JSON.

{{% docs/reference %}}
[user-and-team-management]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
[user-and-team-management]: "/docs/grafana-cloud/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
{{% /docs/reference %}}
