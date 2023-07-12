---
aliases:
  - add-datadog/
  - /docs/oncall/latest/integrations/available-integrations/configure-datadog/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-datadog/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - datadog
title: Datadog
weight: 500
---

# Datadog integration for Grafana OnCall

The Datadog integration for Grafana OnCall handles ticket events sent from Datadog webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin]({{< relref "user-and-team-management" >}}) to be able to create integrations in Grafana OnCall.

## Configuring Grafana OnCall to Receive Alerts from Datadog

1. In the **Integrations** tab, click **+ New integration**.
2. Select **Datadog** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.

## Configuring Datadog to Send Alerts to Grafana OnCall

1. Navigate to the Integrations page from the sidebar
2. Search for webhook in the search bar
3. Enter a name for the integration, for example: grafana-oncall-alerts
4. Paste the **OnCall Integration URL**, then save
5. Navigate to the Events page from the sidebar to send the test alert
6. Type @webhook-grafana-oncall-alerts test alert
7. Click the post button
