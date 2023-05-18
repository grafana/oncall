---
aliases:
  - add-alertmanager/
  - /docs/oncall/latest/integrations/available-integrations/configure-alertmanager/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-alertmanager/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - Alertmanager
  - Prometheus
title: Alertmanager integration for Grafana OnCall
weight: 300
---

# Alertmanager integration for Grafana OnCall

The Alertmanager integration for Grafana OnCall handles alerts sent by client applications such as the Prometheus server.

Grafana OnCall provides<!--[grouping](#alertmanager-grouping-amp-oncall-grouping)--> grouping abilities when processing
alerts from Alertmanager, including initial deduplicating, grouping, and routing the alerts to Grafana OnCall.

## Configure Alertmanager integration for Grafana OnCall

You must have an Admin role to create integrations in Grafana OnCall.

1. In the **Integrations** tab, click **+ New integration to receive alerts**.
2. Select **Alertmanager** from the list of available integrations.
3. Follow the instructions in the **How to connect** window to get your unique integration URL and identify next steps.

<!--![123](../_images/connect-new-monitoring.png)-->

## Configure Alertmanager

Update the `receivers` section of your Alertmanager configuration to use a unique integration URL:

```yaml
route:
  receiver: "oncall"
  group_by: [alertname, datacenter, app]

receivers:
  - name: "oncall"
    webhook_configs:
      - url: <integation-url>
        send_resolved: true
```

## Configure grouping with Alertmanager and Grafana OnCall

You can use the alert grouping mechanics of Alertmanager and Grafana OnCall to configure your alert grouping preferences.

Alertmanager offers three alert grouping options:

- `group_by` provides two options, `instance` or `job`.
- `group_wait` sets the length of time to initially wait before sending a notification for a particular group of alerts.
  For example, `group_wait` can be set to 45s.

  Setting a high value for `group_wait` reduces alert noise and minimizes interruption, but it may introduce delays in
  receiving alert notifications. To set an appropriate wait time, consider whether the group of alerts will be the same
  as those previously sent.

- `group_interval` sets the length of time to wait before sending notifications about new alerts that have been added to
  a group of alerts that have been previously alerted on. This setting is usually set to five minutes or more.

  During high alert volume periods, Alertmanager will send alerts at each `group_interval`, which can mean a lot of
  distraction. Grafana OnCall grouping will help manage this in the following ways:

  - Grafana OnCall groups alerts based on the first label of each alert.
  - Grafana OnCall marks an alert group as resolved only when there are fewer than 500 grouped
  alerts, and every `firing` alert with the same labels has a corresponding `resolved` alert
