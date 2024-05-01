---
title: Datadog integration for Grafana OnCall
menuTitle: Datadog
description: Datadog integration reference material for Grafana OnCall.
weight: 0
keywords:
  - OnCall
  - Integrations
  - Alerts
  - AppDynamics
  - Notifications
labels:
  products:
    - cloud
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/references/datadog
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/datadog
  - /docs/grafana-cloud/alerting-and-irm/oncall/integrations/datadog
  - add-datadog/
  - ../integrations/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/datadog
refs:
  user-and-team-management:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/user-and-team-management/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/user-and-team-management/
---

# Datadog integration for Grafana OnCall

{{< admonition type="note" >}}
This integration is available exclusively on Grafana Cloud.
{{< /admonition >}}

The Datadog integration for Grafana OnCall handles ticket events sent from Datadog webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

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
