---
aliases:
  - add-alertmanager/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-alertmanager/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - Alertmanager
  - Prometheus
title: Alertmanager
weight: 300
---

# Alertmanager integration for Grafana OnCall

> ⚠️ A note about **(Legacy)** integrations: We are introducing new AlertManager integration with enhanced grouping and auto-resolve mechanism.
> Integrations that were created before version **VERSION** are marked as **(Legacy)**.
> These integrations are still functional, receiving and escalating alerts, but will be automatically migrated after DEPRECATION_DATE.
> Integration urls will not be changed during the migration, so no changes in AlertManager configuration is required.
> To ensure a smooth transition you can migrate them by yourself now.
> [Here][migration] you can read more about migration process.

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
3. Set `send_resolved` to `true`, so Grafana OnCall can autoresolve alert groups when they are resolved in Alertmanager
4. It is recommended to set `max_alerts` to less than `100` to avoid too big requests.
5. Use this receiver in your route configuration

Here is the example of final configuration:

```yaml
route:
  receiver: "oncall"
  group_by: [alertname, datacenter, app]

receivers:
  - name: "oncall"
    webhook_configs:
      - url: <integation-url>
        send_resolved: true
        max_alerts: 100
```

## Complete the Integration Configuration

Complete configuration by setting routes, templates, maintenances, etc. Read more in
[this section][complete-the-integration-configuration]

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

## Migrating from Legacy AlertManager Integration

Before we were using each alert from AlertManager group as a separate payload:

```json
{
            "labels": {
                "severity": "critical",
                "alertname": "InstanceDown"
            },
            ...
}
```

This behaviour was leading to mismatch in alert state between OnCall and AlertManager and draining of rate-limits,
since each AlertManager alert was counted for them.

We decided to change this behaviour to respect AlertManager grouping by treating AlertManager group as one payload.

```json
{
    "alerts": [...],
    "groupLabels": {"alertname": "InstanceDown"},
    "commonLabels": {"job": "node",  "alertname": "InstanceDown"},
    "groupKey": "{}:{alertname=\"InstanceDown\"}",
    ...
}
```

### How to migrate

1. Go to **Integration Page**, click on three dots on top right, click **Migrate**
2. Confirmation Modal will be shown, read it carefully and proceed with migration.
3. Integration will be updated, integration url will stay the same, templates will be reset.
4. Adjust templates and routes to the new shape of payload.

You can read more about AlertManager Data model [here](https://prometheus.io/docs/alerting/latest/notifications/#data).

{{% docs/reference %}}
[user-and-team-management]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
[user-and-team-management]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/user-and-team-management"

[complete-the-integration-configuration]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/integrations#complete-the-integration-configuration"
[complete-the-integration-configuration]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/integrations#complete-the-integration-configuration"

[migration]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/integrations/alertmanager#migrating-from-legacy-alertmanager-integration"
[migration]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/integrations/alertmanager#migrating-from-legacy-alertmanager-integration"
{{% /docs/reference %}}
