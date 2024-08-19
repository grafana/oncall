---
title: Alertmanager integration for Grafana OnCall
menuTitle: Alertmanager
description: Alertmanager integration reference material for Grafana OnCall.
weight: 0
keywords:
  - OnCall
  - Integrations
  - Alerts
  - Alertmanager
  - Prometheus
  - Notifications
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/references/alertmanager
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/alertmanager
  - /docs/grafana-cloud/alerting-and-irm/oncall/integrations/alertmanager
  - add-alertmanager/
  - ../integrations/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/alertmanager
refs:
  complete-the-integration-configuration:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/integrations/integration-management/#customize-the-integration
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/integrations/#customize-the-integration
  user-and-team-management:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/user-and-team-management/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/user-and-team-management/
  data_webhook_template:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL VERSION>/configure/integrations/outgoing-webhooks/#outgoing-webhook-templates
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/outgoing-webhooks/#outgoing-webhook-templates
  trigger_webhook_template:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL VERSION>/configure/integrations/outgoing-webhooks/#using-trigger-template-field
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL VERSION>/configure/integrations/outgoing-webhooks/#using-trigger-template-field
---

# Alertmanager integration for Grafana OnCall

{{< admonition type="note" >}}
⚠️ **Legacy** integration ⚠️ Integrations that were created before version 1.3.21 (1 August 2023) were marked as **(Legacy)** and migrated.
These integrations are receiving and escalating alerts, but some manual adjustments may be required.
{{< /admonition >}}

The Alertmanager integration handles alerts from [Prometheus Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/).
This integration is the recommended way to send alerts from Prometheus deployed in your infrastructure, to Grafana OnCall.

> **Pro tip:** Create one integration per team, and configure alertmanager labels selector to send alerts only related to that team

## Configuring Grafana OnCall to Receive Alerts from Prometheus Alertmanager

1. In the **Integrations** tab, click **+ New integration**.
2. Select **Alertmanager Prometheus** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.
   You will need it when configuring Alertmanager.

## Configuring Alertmanager to Send Alerts to Grafana OnCall

1. Add a new [Webhook](https://prometheus.io/docs/alerting/latest/configuration/#webhook_config) receiver to `receivers`
   section of your Alertmanager configuration
2. Set `url` to the **OnCall Integration URL** from previous section
   - **Note:** The url has a trailing slash that is required for it to work properly.
3. Set `send_resolved` to `true`, so Grafana OnCall can autoresolve alert groups when they are resolved in Alertmanager
4. It is recommended to set `max_alerts` to less than `100` to avoid requests that are too large.
5. Use this receiver in your route configuration

Here is the example of final configuration:

```yaml
route:
  receiver: "oncall"
  group_by: [alertname, datacenter, app]

receivers:
  - name: "oncall"
    webhook_configs:
      - url: <integration-url>
        send_resolved: true
        max_alerts: 100
```

## Complete the Integration Configuration

Complete configuration by setting routes, templates, maintenances, etc. Read more in
[this section](ref:complete-the-integration-configuration)

## Note about grouping and autoresolution

Grafana OnCall relies on the Alertmanager grouping and autoresolution mechanism to
ensure consistency between alert state in OnCall and AlertManager.
It's recommended to configure [grouping](https://prometheus.io/docs/alerting/latest/alertmanager/#grouping) on the Alertmanager side and use default grouping
and autoresolution templates on the OnCall side. Changing this templates might lead to incorrect
grouping and autoresolution behavior. This is unlikely to be what you want, unless you have disabled
grouping on the AlertManager side.

## Configuring OnCall Heartbeats (optional)

An OnCall heartbeat acts as a monitoring for monitoring systems. If your monitoring is down and stop sending alerts,
Grafana OnCall will notify you about that.

### Configuring Grafana OnCall Heartbeat

1. Go to **Integration Page**, click on three dots on top right, click **Heartbeat settings**
2. Copy **OnCall Heartbeat URL**, you will need it when configuring Alertmanager
3. Set up **Heartbeat Interval**, time period after which Grafana OnCall will start a new alert group if it
   doesn't receive a heartbeat request

### Configuring Alertmanager to send heartbeats to Grafana OnCall Heartbeat

You can configure Alertmanager to regularly send alerts to the heartbeat endpoint. Add `vector(1)` as a heartbeat
generator to `prometheus.yaml`. It will always return true and act like always firing alert, which will be sent to
Grafana OnCall once in a given period of time:

```yaml
groups:
  - name: meta
    rules:
      - alert: heartbeat
        expr: vector(1)
        labels:
          severity: none
        annotations:
          description: This is a heartbeat alert for Grafana OnCall
          summary: Heartbeat for Grafana OnCall
```

Add receiver configuration to `prometheus.yaml` with the **OnCall Heartbeat URL**:

```yaml
  ...
  route:
  ...
      routes:
        - match:
          alertname: heartbeat
        receiver: 'grafana-oncall-heartbeat'
        group_wait: 0s
        group_interval: 1m
        repeat_interval: 50s
  receivers:
    - name: 'grafana-oncall-heartbeat'
    webhook_configs:
      - url: https://oncall-dev-us-central-0.grafana.net/oncall/integrations/v1/alertmanager/1234567890/heartbeat/
        send_resolved: false
```

## Note about legacy integration

Legacy integration was using each alert from AlertManager group as a separate payload:

```json
{
  "labels": {
    "severity": "critical",
    "alertname": "InstanceDown"
  },
  "annotations": {
    "title": "Instance localhost:8081 down",
    "description": "Node has been down for more than 1 minute"
  },
  ...
}
```

This behaviour was leading to mismatch in alert state between OnCall and AlertManager and draining of rate-limits,
since each AlertManager alert was counted separately.

We decided to change this behaviour to respect AlertManager grouping by using AlertManager group as one payload.

```json
{
  "alerts": [...],
  "groupLabels": {
    "alertname": "InstanceDown"
  },
  "commonLabels": {
    "job": "node", 
    "alertname": "InstanceDown"
  },
  "commonAnnotations": {
    "description": "Node has been down for more than 1 minute"
  },
  "groupKey": "{}:{alertname=\"InstanceDown\"}",
  ...
}
```

You can read more about AlertManager Data model [here](https://prometheus.io/docs/alerting/latest/notifications/#data).

### After-migration checklist

> Integration URL will stay the same, so no need to change AlertManager or Grafana Alerting configuration.
> Integration templates will be reset to suit new payload.
> It is needed to adjust routes and outgoing webhooks manually to new payload.

1. Send a new demo alert to the migrated integration.
2. Adjust routes to the new shape of payload. You can use payload of the demo alert from previous step as an example.
3. If outgoing webhooks utilized the alerts payload from the migrated integration in the [trigger](ref:trigger_webhook_template)
or [data](ref:data_webhook_template) template it's needed to adjust them as well.

<img width="1646" alt="Screenshot 2023-12-14 at 1 14 21 PM" src="https://github.com/grafana/oncall/assets/85312870/7e281416-edbc-4384-8d15-7efaec2de311">

<img width="1644" alt="Screenshot 2023-12-14 at 1 14 32 PM" src="https://github.com/grafana/oncall/assets/85312870/b62cfa1d-2ff6-4b46-9cec-459b14cd1996">
