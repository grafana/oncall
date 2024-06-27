---
title: Insight logs and metrics
menuTitle: Insight logs and metrics
description: Explore Grafana OnCall insights and metrics.
weight: 700
keywords:
  - OnCall
  - Audit logs
  - Insight logs
  - Loki
  - Prometheus
  - Alerts
canonical: https://grafana.com/docs/oncall/latest/manage/insights-and-metrics/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/manage/insights-and-metrics/
  - /docs/grafana-cloud/alerting-and-irm/oncall/insights-and-metrics/
  - ../insights-and-metrics/ # /docs/oncall/<ONCALL_VERSION>/insights-and-metrics/
refs:
  grafana-oncall-api:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/oncall-api-reference/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/
---

# Insight Logs and Metrics

## Metrics

Grafana OnCall Metrics represents certain parameters, such as:

- A total count of alert groups for each integration in every state (firing, acknowledged, resolved, silenced).
It is a gauge, and its name has the suffix `alert_groups_total`
- Response time on alert groups for each integration (mean time between the start and first action of all alert groups
for the last 7 days in selected period). It is a histogram, and its name has the suffix `alert_groups_response_time`
with the histogram suffixes such as `_bucket`, `_sum` and `_count`
- A total count of alert groups users were notified of for each user. It is a counter, and its name has the suffix
`user_was_notified_of_alert_groups_total`

You can find more information about metrics types in the [Prometheus documentation](https://prometheus.io/docs/concepts/metric_types).

To retrieve Prometheus metrics use PromQL. If you are not familiar with PromQL, check this [documentation](https://prometheus.io/docs/prometheus/latest/querying/basics/).

### For Grafana Cloud customers

OnCall application metrics are collected in preinstalled `grafanacloud_usage` datasource and are available for every
cloud instance.

Metrics have prefix `grafanacloud_oncall_instance`, e.g. `grafanacloud_oncall_instance_alert_groups_total`,
`grafanacloud_oncall_instance_alert_groups_response_time_seconds_bucket` and
`grafanacloud_oncall_instance_user_was_notified_of_alert_groups_total`.

### For open source customers

To collect OnCall application metrics you need to set up Prometheus and add it to your Grafana instance as a datasource.
You can find more information about Prometheus setup in the [OSS documentation](https://github.com/grafana/oncall#readme)

Metrics will have the prefix `oncall`, e.g. `oncall_alert_groups_total`, `oncall_alert_groups_response_time_seconds_bucket`
and `oncall_user_was_notified_of_alert_groups_total`.

Your metrics may also have additional labels, such as `pod`, `instance`, `container`, depending on your Prometheus setup.

### Metrics: Alert groups total

This metric has the following labels:

| Label Name    |                                 Description                                   |
|---------------|:-----------------------------------------------------------------------------:|
| `id`          | ID of Grafana instance (stack)                                                |
| `slug`        | Slug of Grafana instance (stack)                                              |
| `org_id`      | ID of Grafana organization                                                    |
| `team`        | Team name                                                                     |
| `integration` | OnCall Integration name                                                       |
| `service_name`| Value of Alert group `service_name` label                                     |
| `state`       | Alert groups state. May be `firing`, `acknowledged`, `resolved` and `silenced`|

**Query example:**

Get the number of alert groups in "firing" state in integration "Grafana Alerting" in Grafana stack "test_stack":

```promql
grafanacloud_oncall_instance_alert_groups_total{slug="test_stack", integration="Grafana Alerting", state="firing"}
```

### Metrics: Alert groups response time

This metric has the following labels:

| Label Name    |                                 Description                                    |
|---------------|:------------------------------------------------------------------------------:|
| `id`          | ID of Grafana instance (stack)                                                 |
| `slug`        | Slug of Grafana instance (stack)                                               |
| `org_id`      | ID of Grafana organization                                                     |
| `team`        | Team name                                                                      |
| `integration` | OnCall Integration name                                                        |
| `service_name`| Value of Alert group `service_name` label                                      |
| `le`          | Histogram bucket value in seconds. May be `60`, `300`, `600`, `3600` and `+Inf`|

**Query example:**

Get the number of alert groups with response time more than 10 minutes (600 seconds) in integration "Grafana Alerting"
in Grafana stack "test_stack":

```promql
grafanacloud_oncall_instance_alert_groups_response_time_seconds_bucket{slug="test_stack", integration="Grafana Alerting", le="600"}
```

### Metrics: Alert groups user was notified of

This metric has the following labels:

| Label Name    |                                 Description                                   |
|---------------|:-----------------------------------------------------------------------------:|
| `id`          | ID of Grafana instance (stack)                                                |
| `slug`        | Slug of Grafana instance (stack)                                              |
| `org_id`      | ID of Grafana organization                                                    |
| `username`    | User username                                                                 |

**Query example:**

Get the number of alert groups user with username "alex" was notified of in Grafana stack "test_stack":

```promql
grafanacloud_oncall_instance_user_was_notified_of_alert_groups_total{slug="test_stack", username="alex"}
```

### Dashboard

You can find the "OnCall Insights" dashboard in the list of your dashboards in the folder `General`, it has the tag
`oncall`. In the datasource dropdown select your Prometheus datasource (for Cloud customers it's `grafanacloud_usage`).
You can filter data by your Grafana instances, teams and integrations.

To re-import OnCall metrics dashboard go to `Administration` -> `Plugins` page, find OnCall in the plugins list, open
`Dashboards` tab at the OnCall plugin settings page and click "Re-import" near "OnCall Metrics". After that you can find
the "OnCall Metrics" dashboard in your dashboards list.

Be aware: if you have made changes to the dashboard, they will be lost after re-importing or after the plugin update.
To save your changes go to the "OnCall Metrics" dashboard settings, click "Save as" and save a copy of the dashboard.

You can also view Insights from Grafana OnCall.

To view Insights, complete the following steps.

1. Open Grafana OnCall.
2. Click the **Insights** sub-section in the navigation menu.

## Logs

> **Note:** Grafana OnCall insight logs are available in Grafana Cloud only.
We're in the process of rolling out Insight Logs to all customers,
if you don't see insight logs in your Grafana Cloud stack, please reach out to support.

Grafana OnCall Insights Logs represents certain activities, such as when:

- A user creates, updates, or deletes a resource.
- A Maintenance mode is started or finished for an integration.
- A user configures a ChatOps integration.

This configuration is done for you in Grafana Cloud with [Usage Insights Loki data source](https://grafana.com/docs/grafana-cloud/billing-and-usage/usage-insights/#usage-insights-loki-data-source).
You can use this query to retrieve all logs related to your OnCall instance.

```logql
{instance_type="oncall"} | logfmt | __error__=``
```

### Resource logs

Logs are created each time a user modifies any resource in Grafana OnCall.

These logs will have `action_type=resource` field and can be retrieved with following query:

```logql
{instance_type="oncall"} | logfmt | __error__=`` | action_type = `resource`
```

#### Format

Logs contain the following fields, where the fields followed by * are always available, and the others depend on the logged event:

| Field Name            |                                 Description                                  |
|-----------------------|:----------------------------------------------------------------------------:|
| `action_name`*        | Type of the resource action, which can be `created`, `updated` or `deleted`. |
| `action_type`*        |      Insight Log type. For resource insight logs it will be `resource`.      |
| `author`*             |                    Username of user who performed action.                    |
| `author_id`*          |                       ID of user who performed action.                       |
| `prev_state`          |                JSON representation of resource before update.                |
| `new_state`           |                JSON representation of resource after update.                 |
| `resource_id`*        |                            ID of target resource.                            |
| `resource_name`*      |                           Name of target resource.                           |
| `resource_type`*      |             Type of target resource (See available types below).             |
| `team`*               |                   Name of team to which resource belongs.                    |
| `team_id`             |                    ID of team to which resource belongs.                     |
| `integration`         |                Name of integration to which resource belongs.                |
| `integration_id`      |                 ID of integration to which resource belongs.                 |
| `escalation_chain`    |                   Name of team to which resource belongs.                    |
| `escalation_chain_id` |                    ID of team to which resource belongs.                     |
| `schedule`            |                 Name of schedule to which resource belongs.                  |
| `schedule_id`         |                  ID of schedule to which resource belongs .                  |

resource types are: `integration_heartbeat`, `escalation_chain`, `integration`, `outgoing_webhook`,
`escalation_policy`, `public_api_token`, `schedule_export_token`,`user_schedule_export_token`,
`oncall_shift`, `web_schedule`, `ical_schedule`, `calendar_schedule`, `shift_swap_request`, `organization`,
`user`, `webhook`.

### Maintenance logs

Logs are created every time when a maintenance mode is started or finished for an integration.

These logs will have `action_type=maintenace` field and can be retrieved with following query:

```logql
{instance_type="oncall"} | logfmt | __error__=`` | action_type = `maintenance`
```

#### Format

Logs of maintenance insights contain the following fields, where the fields followed by * are always available, and the others depend on the logged event:

| Field Name          |                               Description                                |
|---------------------|:------------------------------------------------------------------------:|
| `action_name`*      |   Name of the maintenance action, which can be `started` or `finised`.   |
| `action_type`*      | Insight Log type. For Maintenance Insight logs it will be `maintenance`. |
| `author`            |                  Username of user who performed action.                  |
| `author_id`         |             Grafana OnCall ID of user who performed action.              |
| `maintenance_mode`* |      Type of the maintenance, which can be `maintenance` or `debug`      |
| `resource_id`*      |                        ID of target integration.                         |
| `resource_name`*    |                       Name of target integration.                        |
| `team`*             |                Name of team to which integration belongs.                |
| `team_id`           |                 ID of team to which integration belongs.                 |

### ChatOps logs

Logs are created when user modifies ChatOps settings.

These log lines will have `action_type=chat_ops` field and can be retrieved with following query:

```logql
{instance_type="oncall"} | logfmt | __error__=`` | action_type = `chat_ops`
```

#### Format

Logs of chatops insight logs contain the following fields, where the fields followed by * are always available, and the others depend on the logged event:

| Field Name       |                                   Description                                    |
|------------------|:--------------------------------------------------------------------------------:|
| `action_name`*   |             Name of the chatops action (See available names below).              |
| `action_type`*   |     Insight Log type. For Chatops Insight logs it always will be `chat_ops`.     |
| `author`*        |                      Username of user who performed action                       |
| `author_id`*     |                  Grafana OnCall ID of user who performed action                  |
| `сhat_ops_type`* | Type of chatops integration. Can be `telegram`, `slack`, `msteams`, `mobile_app` |
| `linked_user`    |                  Username of user linked to chatops integration                  |
| `linked_user_id` |             Grafana OnCall ID of user linked to chatops integration              |
| `channel_name`   |                Name of the channel linked to chatops integration                 |
| `prev_channel`   |                      Name of team to which resource belongs                      |
| `new_channel`    |               Grafana OnCall ID of team to which resource belongs                |

chatops action names: `workspace_connected`, `workspace_disconnected`, `channel_connected`, `channel_disconnected`, `user_linked`, `used_unlinked`, `default_channel_changed`.

### Examples

Here is some examples of practical queries to Grafana OnCall insight logs.
LogQL is used to retrieve them.
If you aren't familiar with LogQL, refer to [LogQL: Log query language](https://grafana.com/docs/loki/latest/query/).

Resource IDs are used a lot in insight logs. You can find them in web ui (example for integration):

1. Open Grafana OnCall.
2. Navigate to resource.
3. The URL looks like `https://<YOUR_STACK_SLUG>/a/grafana-oncall-app/integrations/C5VXMIFKKP67K`.
4. Integration ID is `C5VXMIFKKP67K`.

Alternatively you can find the resource ID using the[Grafana OnCall API](ref:grafana-oncall-api) or browser dev tools.

Actions performed by user:

```logql
{instance_type="oncall"} | logfmt | __error__=`` | action_type = `resource` and author="<username>"
```

Actions performed with all schedules:

```logql
{instance_type="oncall"} | logfmt | __error__=`` | action_type = `resource` and (resource_type=`web_schedule` or resource_type=`calendar_schedule` or resource_type=`ical_schedule`)
```

Changes of escalation policies for escalation chain:

```logql
{instance_type="oncall"} | logfmt | __error__=`` | action_type = `resource` and resource_type=`escalation_policy` and escalation_chain_id=`<ESCALATION_CHAIN_ID>`
```

Maintenance events for integration:

```logql
{instance_type="oncall"} | logfmt | __error__=`` | action_type = `maintenance` and resource_id=`CSA67IQW2NMVL`
```

Actions performed with slack chatops integration:

```logql
{instance_type="oncall"} | logfmt | __error__=`` | action_type = `chat_ops` and chat_ops_type=`slack`
```
