---
title: Fabric integration for Grafana OnCall
menuTitle: Fabric
description: Fabric integration reference material for Grafana OnCall.
weight: 0
keywords:
  - OnCall
  - Integrations
  - Alerts
  - Fabric
  - Notifications
labels:
  products:
    - cloud
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/references/fabric
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/fabric
  - /docs/grafana-cloud/alerting-and-irm/oncall/integrations/fabric
  - add-fabric/
  - ../integrations/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/fabric
refs:
  user-and-team-management:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/user-and-team-management/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/user-and-team-management/
---

# Fabric integration for Grafana OnCall

{{< admonition type="note" >}}
This integration is available exclusively on Grafana Cloud.
{{< /admonition >}}

The Fabric integration for Grafana OnCall handles ticket events sent from Fabric webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

## Configuring Grafana OnCall to Receive Alerts from Fabric

1. In the **Integrations** tab, click **+ New integration**.
2. Select **Fabric** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.

## Configuring Fabric to Send Alerts to Grafana OnCall

1. Go to <https://www.fabric.io/settings/apps>
2. Choose your application
3. Navigate to Service Hooks -> WebHook
4. Enter URL: **OnCall Integration URL**
5. Click Verify
6. Choose "SEND IMPACT CHANGE ALERTS" and "ALSO SEND NON-FATAL ALERTS"
