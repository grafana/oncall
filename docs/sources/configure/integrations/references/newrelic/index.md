---
title: New Relic integration for Grafana OnCall
menuTitle: New Relic
description: New Relic integration reference material for Grafana OnCall.
weight: 0
keywords:
  - OnCall
  - Integrations
  - Alerts
  - New Relic
  - Notifications
labels:
  products:
    - cloud
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/references/newrelic
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/newrelic
  - /docs/grafana-cloud/alerting-and-irm/oncall/integrations/newrelic
  - add-newrelic/
  - ../integrations/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/newrelic
refs:
  user-and-team-management:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/user-and-team-management/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/user-and-team-management/
---

# New Relic integration for Grafana OnCall

{{< admonition type="note" >}}
This integration is available exclusively on Grafana Cloud.
{{< /admonition >}}

The New Relic integration for Grafana OnCall handles ticket events sent from New Relic webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

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
