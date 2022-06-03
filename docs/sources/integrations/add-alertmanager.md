+++
title = "Configure alert notifications with Alertmanager"
keywords = ["Grafana Cloud", "Alerts", "Notifications", "on-call", "Alertmanager", "Prometheus"]
aliases = ["/docs/grafana-cloud/oncall/integrations/add-alertmanager/"]
weight = 500
+++

# Alertmanager (Prometheus)

The Alertmanager integration handles alerts sent by client applications such as the Prometheus server. 

Grafana OnCall provides<!--[grouping](#alertmanager-grouping-amp-oncall-grouping)--> grouping abilities when processing alerts from Alertmanager, including initial deduplicating, grouping, and routing the alerts to Grafana OnCall.

## Connect Alertmanager to Grafana OnCall

You must have an Admin role to connect to Grafana OnCall.

1. Navigate to the **Integrations** tab in Grafana OnCall. 

1. Click on the Alertmanager icon.

1. Follow the instructions that display in the dialog box to find a unique integration URL in the monitoring configuration.

<!--![123](../_images/connect-new-monitoring.png)-->

## Configure Alertmanager

Update the `receivers` section of your Alertmanager configuration to use a unique integration URL:
```
route:
  receiver: 'oncall'
  group_by: [alertname, datacenter, app]

receivers:
- name: 'oncall'
  webhook_configs:
  - url: <integation-url>
    send_resolved: true
```

## Configure grouping with Alertmanager and Grafana OnCall

You can use the grouping mechanics of Alertmanager and Grafana OnCall to configure settings for groups of alert notifications. 

Alertmanager offers three grouping settings:

- `group_by` provides two options, `instance` or `job`.
- `group_wait` sets the length of time to initially wait before sending a notification for a particular group of alerts. For example, `group_wait` can be set to 45s.

    Setting a high value for `group_wait` reduces alert noise and minimizes interruption, but it may introduce longer delays in receiving alert notifications. To set an appropriate wait time, consider whether the group of alerts will be the same as those previously sent.

- `group_interval` sets the length of time to wait before sending notifications about new alerts that have been added to a group of alerts that have been previously alerted on. This setting is usually set to five minutes or more.

    During high alert volume periods, Alertmanager will send alerts at each `group_interval`, which can mean a lot of distraction. Grafana OnCall grouping will help manage this in the following ways:

    - Grafana OnCall groups alerts based on the first label of each alert. 

    - Grafana OnCall marks an incident as resolved only when the amount of grouped alerts with state `resolved` equals the amount of alerts with state `firing`.
