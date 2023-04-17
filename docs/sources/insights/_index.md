# Grafana OnCall insight logs

> **Note:** Grafana OnCall insight logs are available in Grafana Cloud only.
We're in process of rolling Insight Logs to all customers,
if you don't see insight logs in your Grafana cloud stack, please reach out to support.

Grafana OnCall insights logs represents certain activities, such as:

- A user creates, updates or deletes resource.
- A Maintenance mode is started or finished for an integration.
- A user configure ChatOps integration.

This configuration is done for you in Grafana Cloud with [Usage Insights Loki data source](https://grafana.com/docs/grafana-cloud/billing-and-usage/usage-insights/#usage-insights-loki-data-source).
You can use this query to retrieve all logs related to your OnCall instance.

```logql
{instance_type="oncall"} | logfmt | __error__=``
```

## Resource insight logs

Logs are created each time user modifies any resource in Grafana OnCall.

These logs will have `action_type=resource` field and can be retrieved with following query:

```logql
{instance_type="oncall"} | logfmt | __error__=`` | action_type = `resource`
```

### Format

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
`oncall_shift`, `web_schedule`, `ical_schedule`, `calendar_schedule`, `organization`, `user`, `webhook`.

## Maintenance insight logs

Logs are created every time when a maintenance mode is started or finished for an integration.

These logs will have `action_type=maintenace` field and can be retrieved with following query:

```logql
{instance_type="oncall"} | logfmt | __error__=`` | action_type = `maintenance`
```

### Format

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

## ChatOps insight logs

Logs are created when user modifies ChatOps settings.

These log lines will have `action_type=chat_ops` field and can be retrieved with following query:

```logql
{instance_type="oncall"} | logfmt | __error__=`` | action_type = `chat_ops`
```

### Format

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

## Examples

Here is some examples of practical queries to Grafana OnCall insight logs.
LogQL is used to retrieve them, If you are not familiar with LogQL check this [documentation](https://grafana.com/docs/loki/latest/logql/).

Resource IDs are used a lot in insight logs. You can find them in web ui (example for integration):

1. Open Grafana OnCall.
2. Navigate to resource.
3. The URL looks like `https://<YOUR_STACK_SLUG>/a/grafana-oncall-app/integrations/C5VXMIFKKP67K`.
4. Integration ID is `C5VXMIFKKP67K`.

Alternatively you can find resource ID using public [API](https://grafana.com/docs/oncall/latest/oncall-api-reference/) or browser dev tools.

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
