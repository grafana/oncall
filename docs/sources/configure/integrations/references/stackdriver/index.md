---
title: Stackdriver integration for Grafana OnCall
menuTitle: Stackdriver
description: Learn how to configure the Stackdriver integration for Grafana OnCall.
weight: 0
keywords:
  - OnCall
  - Integrations
  - Alerts
  - Stackdriver
  - Notifications
labels:
  products:
    - cloud
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/references/stackdriver
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/stackdriver
  - /docs/grafana-cloud/alerting-and-irm/oncall/integrations/stackdriver
  - /docs/oncall/latest/integrations/stackdriver/
  - ../integrations/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/stackdriver
refs:
  user-and-team-management:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/user-and-team-management/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/user-and-team-management/
---

# Stackdriver integration for Grafana OnCall

{{< admonition type="note" >}}
This integration is available exclusively on Grafana Cloud.
{{< /admonition >}}

The Stackdriver integration for Grafana OnCall handles ticket events sent from Stackdriver webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

## Configuring Grafana OnCall to Receive Alerts from Stackdriver

1. In the **Integrations** tab, click **+ New integration**.
2. Select **Stackdriver** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.

## Configuring Stackdriver to Send Alerts to Grafana OnCall

1. Create a notification channel in Stackdriver by navigating to Workspace Settings -> WEBHOOKS -> Add Webhook **OnCall Integration URL**

2. Create and alert in Stackdriver by navigating to Alerting -> Policies -> Add Policy -> Choose Notification Channel using the channel set up in step 1
