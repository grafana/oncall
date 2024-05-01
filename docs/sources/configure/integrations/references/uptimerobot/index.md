---
title: UptimeRobot integration for Grafana OnCall
menuTitle: UptimeRobot
description: Learn how to configure the UptimeRobot integration for Grafana OnCall.
weight: 0
keywords:
  - OnCall
  - Integrations
  - Alerts
  - UptimeRobot
  - Notifications
labels:
  products:
    - cloud
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/references/uptimerobot
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/uptimerobot
  - /docs/grafana-cloud/alerting-and-irm/oncall/integrations/uptimerobot
  - /docs/oncall/latest/integrations/available-integrations/configure-uptimerobot
  - add-uptimerobot/
  - ../integrations/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/uptimerobot
refs:
  user-and-team-management:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/user-and-team-management/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/user-and-team-management/
---



# UptimeRobot integration for Grafana OnCall

{{< admonition type="note" >}}
This integration is available exclusively on Grafana Cloud.
{{< /admonition >}}

The UptimeRobot integration for Grafana OnCall handles ticket events sent from UptimeRobot webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

## Configuring Grafana OnCall to Receive Alerts from UptimeRobot

1. In the **Integrations** tab, click **+ New integration**.
2. Select **UptimeRobot** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.

## Configuring UptimeRobot to Send Alerts to Grafana OnCall

1. Open <https://uptimerobot.com> and log in
1. Go to My Settings > Add Alert Contact and set the following fields:
1. Alert Contact Type: Webhook
1. Friendly Name: Grafana OnCall
1. URL to Notify: **OnCall Integration URL**
   POST Value (JSON Format):

```json
{
  "monitorURL": "monitorURL",
  "monitorFriendlyName": "monitorFriendlyName",
  "alertType": "alertType",
  "alertTypeFriendlyName": "alertTypeFriendlyName",
  "alertDetails": "alertDetails",
  "alertDuration": "alertDuration",
  "sslExpiryDate": "sslExpiryDate",
  "sslExpiryDaysLeft": "sslExpiryDaysLeft"
}
```

1. Flag Send as JSON
1. Click Save Changes and Close
1. Send Test Alert to Grafana OnCall

1. Click Add New Monitor
1. Monitor Type HTTP(s)
1. Friendly Name Test OnCall
1. Set URL to <http://devnull.oncall.io> or any other non-existent domain
1. Click Checkbox next to OnCall Alert Contact (created in the previous step)
1. Click Create Monitor
