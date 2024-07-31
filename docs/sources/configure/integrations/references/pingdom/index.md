---
title: Pingdom integration for Grafana OnCall
menuTitle: Pingdom
description: Pingdom integration reference material for Grafana OnCall.
weight: 0
keywords:
  - OnCall
  - Integrations
  - Alerts
  - Pingdom
  - Notifications
labels:
  products:
    - cloud
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/references/pingdom
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/pingdom
  - /docs/grafana-cloud/alerting-and-irm/oncall/integrations/pingdom
  - add-pingdom/
  - ../integrations/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/pingdom
refs:
  user-and-team-management:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/user-and-team-management/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/user-and-team-management/
---

# Pingdom integration for Grafana OnCall

{{< admonition type="note" >}}
This integration is available exclusively on Grafana Cloud.
{{< /admonition >}}

The Pingdom integration for Grafana OnCall handles ticket events sent from Pingdom webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

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
