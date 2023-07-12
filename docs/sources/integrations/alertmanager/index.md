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

> You must have the [role of Admin]({{< relref "user-and-team-management" >}}) to be able to create integrations in Grafana OnCall.

The Alertmanager integration handles alerts from [Prometheus Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/).
This integration is the recommended way to send alerts from Prometheus deployed in your infrastructure, to Grafana OnCall.

> **Pro tip:** Create one integration per team, and configure alertmanager labels selector to send alerts only related to that team

## Configuring Grafana OnCall to Receive Alerts from Prometheus Alertmanager

1. In the **Integrations** tab, click **+ New integration**.
2. Select **Alertmanager Prometheus** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.
You will need it when configuring Alertmanager.

<!--![123](../_images/connect-new-monitoring.png)-->

## Configuring Alertmanager to Send Alerts to Grafana OnCall

1. Add a new [Webhook](https://prometheus.io/docs/alerting/latest/configuration/#webhook_config) receiver to `receivers`
section of your Alertmanager configuration
2. Set `url` to the **OnCall Integration URL** from previous section
3. Set `send_resolved` to `true`, so Grafana OnCall can autoresolve alert groups when they are resolved in Alertmanager
4. It is recommended to set `max_alerts` to less than `300` to avoid rate-limiting issues
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
        max_alerts: 300
```

## Complete the Integration Configuration

Complete configuration by setting routes, templates, maintenances, etc. Read more in
[this section]({{< relref "../../integrations/#complete-the-integration-configuration" >}})

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
