---
aliases:
  - add-uptimerobot/
  - /docs/oncall/latest/integrations/available-integrations/configure-uptimerobot/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-uptimerobot/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - uptimerobot
labels:
  products:
    - cloud
title: UptimeRobot
weight: 500
---

# UptimeRobot integration for Grafana OnCall

> This integration is not available in OSS version

The UptimeRobot integration for Grafana OnCall handles ticket events sent from UptimeRobot webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin][user-and-team-management] to be able to create integrations in Grafana OnCall.

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

{{% docs/reference %}}
[user-and-team-management]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
[user-and-team-management]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/user-and-team-management"
{{% /docs/reference %}}
