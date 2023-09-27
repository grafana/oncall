---
aliases:
  - add-fabric/
  - /docs/oncall/latest/integrations/available-integrations/configure-fabric/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-fabric/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - fabric
labels:
  products:
    - cloud
title: Fabric
weight: 500
---

# Fabric integration for Grafana OnCall

> This integration is not available in OSS version

The Fabric integration for Grafana OnCall handles ticket events sent from Fabric webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin][user-and-team-management] to be able to create integrations in Grafana OnCall.

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

{{% docs/reference %}}
[user-and-team-management]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
[user-and-team-management]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/user-and-team-management"
{{% /docs/reference %}}
