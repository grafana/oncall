---
aliases:
  - add-stackdriver/
  - /docs/oncall/latest/integrations/available-integrations/configure-stackdriver/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-stackdriver/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - stackdriver
title: Stackdriver
weight: 500
---

# Stackdriver integration for Grafana OnCall

The Stackdriver integration for Grafana OnCall handles ticket events sent from Stackdriver webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin][user-and-team-management] to be able to create integrations in Grafana OnCall.

## Configuring Grafana OnCall to Receive Alerts from Stackdriver

1. In the **Integrations** tab, click **+ New integration**.
2. Select **Stackdriver** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.

## Configuring Stackdriver to Send Alerts to Grafana OnCall

1. Create a notification channel in Stackdriver by navigating to Workspace Settings -> WEBHOOKS -> Add Webhook **OnCall Integration URL**

2. Create and alert in Stackdriver by navigating to Alerting -> Policies -> Add Policy -> Choose Notification Channel using the channel set up in step 1

<!-- markdownlint-disable MD033 -->
{{% docs/reference %}}
[user-and-team-management]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
[user-and-team-management]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/user-and-team-management"
{{% /docs/reference %}}
<!-- markdownlint-enable MD033 -->

