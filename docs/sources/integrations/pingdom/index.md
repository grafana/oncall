---
aliases:
  - add-pingdom/
  - /docs/oncall/latest/integrations/available-integrations/configure-pingdom/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-pingdom/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - pingdom
title: Pingdom
weight: 500
---

# Pingdom integration for Grafana OnCall

The Pingdom integration for Grafana OnCall handles ticket events sent from Pingdom webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin][user-and-team-management] to be able to create integrations in Grafana OnCall.

## Configuring Grafana OnCall to Receive Alerts from Pingdom

1. In the **Integrations** tab, click **+ New integration**.
2. Select **Pingdom** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.

## Configuring Pingdom to Send Alerts to Grafana OnCall

1. Go to <https://my.pingdom.com/integrations/settings>
2. Click "Add Integration".
3. Type: Webhook. Name: `Grafana OnCall`. URL: **OnCall Integration URL**
4. Go to "Reports" -> "Uptime" -> "Edit Check".
5. Select `Grafana OnCall` integration in the bottom.
6. Click "Modify Check" to save.

{{% docs/reference %}}
[user-and-team-management]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
[user-and-team-management]: "/docs/grafana-cloud/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
{{% /docs/reference %}}
