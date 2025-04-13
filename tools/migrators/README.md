# Grafana OnCall migrator tools

These tools will help you to migrate from various on-call tools to Grafana OnCall.

Currently the migration tool supports migrating from:

- PagerDuty
- Splunk OnCall (VictorOps)
- Opsgenie

## Getting Started

1. Make sure you have `docker` installed and running
2. Build the docker image: `docker build -t oncall-migrator .`
3. Obtain a Grafana OnCall API token and API URL on the "Settings" page of your Grafana OnCall instance
4. Depending on which tool you are migrating from, see more specific instructions there:
   - [PagerDuty](#prerequisites)
   - [Splunk OnCall](#prerequisites-1)
   - [Opsgenie](#prerequisites-2)
5. Run a [migration plan](#migration-plan)
6. If you are pleased with the results of the migration plan, run the tool in [migrate mode](#migration)

### Migration Plan

Before starting the migration process, it's useful to see a migration plan by running the tool in `plan` mode:

#### PagerDuty

```shell
docker run --rm \
-e MIGRATING_FROM="pagerduty" \
-e MODE="plan" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
oncall-migrator
```

#### Splunk OnCall

```shell
docker run --rm \
-e MIGRATING_FROM="splunk" \
-e MODE="plan" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e SPLUNK_API_ID="<SPLUNK_API_ID>" \
-e SPLUNK_API_KEY="<SPLUNK_API_KEY>" \
oncall-migrator
```

#### Opsgenie

```shell
docker run --rm \
-e MIGRATING_FROM="opsgenie" \
-e MODE="plan" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e OPSGENIE_API_KEY="<OPSGENIE_API_KEY>" \
oncall-migrator
```

Please read the generated report carefully since depending on the content of the report, some resources
could be not migrated and some existing Grafana OnCall resources could be deleted.

```text
User notification rules report:
    ✅ John Doe (john.doe@example.com) (existing notification rules will be preserved)
    ❌ Ben Thompson (ben@example.com) — no Grafana OnCall user found with this email

Schedule report:
    ✅ Support (existing schedule with name 'Support' will be deleted)
    ✅ Support-shadow
    ❌ DevOps — schedule references unmatched users
        ❌ Ben Thompson (ben@example.com) — no Grafana OnCall user found with this email

Escalation policy report:
    ✅ Support
    ❌ DevOps Escalation Policy — policy references unmatched users and schedules with unmatched users
        ❌ Ben Thompson (ben@example.com) — no Grafana OnCall user found with this email
        ❌ DevOps — schedule references unmatched users

Integration report:
    ✅ Support - Prometheus (existing integration with name 'Support - Prometheus' will be deleted)
    ❌ DevOps - Prometheus — escalation policy 'DevOps Escalation Policy' references unmatched users or schedules
    with unmatched users
    ❌ DevOps - Email — cannot find appropriate Grafana OnCall integration type
```

### Migration

Once you are happy with the migration report, start the migration by setting the `MODE` environment variable to `migrate`:

#### PagerDuty

```shell
docker run --rm \
-e MIGRATING_FROM="pagerduty" \
-e MODE="migrate" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
oncall-migrator
```

#### Splunk OnCall

```shell
docker run --rm \
-e MIGRATING_FROM="splunk" \
-e MODE="migrate" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e GRAFANA_PASSWORD="<GRAFANA_PASSWORD>" \
-e SPLUNK_API_ID="<SPLUNK_API_ID>" \
-e SPLUNK_API_KEY="<SPLUNK_API_KEY>" \
oncall-migrator
```

#### Opsgenie

```shell
docker run --rm \
-e MIGRATING_FROM="opsgenie" \
-e MODE="migrate" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e OPSGENIE_API_KEY="<OPSGENIE_API_KEY>" \
oncall-migrator
```

When performing a migration, only resources that are marked with ✅ or ⚠️ on the plan stage will be migrated.
The migrator is designed to be idempotent, so it's safe to run it multiple times. On every migration run, the tool will
check if the resource already exists in Grafana OnCall and will delete it before creating a new one.

## PagerDuty

### Overview

Resources that can be migrated using this tool:

- User notification rules
- On-call schedules
- Escalation policies
- Services (integrations)
- Event rules (experimental, only works with global event rulesets)

### Limitations

- Not all integration types are supported
- Delays between migrated notification/escalation rules could be slightly different from original.
  E.g. if you have a 4-minute delay between rules in PagerDuty, the resulting delay in Grafana OnCall will be 5 minutes
- Manual changes to PD configuration may be required to migrate some resources

### Prerequisites

- Obtain a PagerDuty API **user token**: <https://support.pagerduty.com/docs/api-access-keys#generate-a-user-token-rest-api-key>

### Migrate unsupported integration types

It's possible to migrate unsupported integration types to [Grafana OnCall incoming webhooks](https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-webhook/).
To enable this feature, set env variable `UNSUPPORTED_INTEGRATION_TO_WEBHOOKS` to `true`:

```shell
docker run --rm \
-e MIGRATING_FROM="pagerduty" \
-e MODE="migrate" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
-e UNSUPPORTED_INTEGRATION_TO_WEBHOOKS="true" \
oncall-migrator
```

Consider modifying [alert templates](https://grafana.com/docs/oncall/latest/alert-behavior/alert-templates/) of the created
webhook integrations to adjust them for incoming payloads.

### Migrate your PagerDuty data while ignoring Grafana users

This scenario may be relevant where you are unable to import your list of Grafana users, but would like to experiment
with Grafana OnCall, using your existing PagerDuty setup as a starting point for experimentation.

If this is relevant to you, you can migrate as such 👇

> [!IMPORTANT]
> As outlined several times in the documentation below, if you first import data into Grafana OnCall without
> including users, make changes to that data within OnCall, and then later re-import the data with users, Grafana OnCall
> will delete and recreate those objects, as part of the subsequent migration.
>
> As a result, any modifications you made after the initial import will be lost.

```bash
# Step 1: run a plan of what will be migrated, ignoring users for now
docker run --rm \
-e MIGRATING_FROM="pagerduty" \
-e MODE="plan" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
-e MIGRATE_USERS="false" \
oncall-migrator

# Step 2. Actually migrate your PagerDuty data, again ignoring users
docker run --rm \
-e MIGRATING_FROM="pagerduty" \
-e MODE="migrate" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
-e MIGRATE_USERS="false" \
oncall-migrator

# Step 3. Optional; import your users from PagerDuty into your Grafana stack using our provided script
# For more information on our script, see "Migrating Users" section below for some more information on
# how users are migrated.
#
# You can use PAGERDUTY_FILTER_USERS to only import specific users if you want to test with a small set.
#
# Alternatively this can be done with other Grafana IAM methods.
# See Grafana's "Plan your IAM integration strategy" docs for more information on this.
# https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/planning-iam-strategy/
docker run --rm \
-e MIGRATING_FROM="pagerduty" \
-e GRAFANA_URL="<GRAFANA_API_URL>" \
-e GRAFANA_USERNAME="<GRAFANA_USERNAME>" \
-e GRAFANA_PASSWORD="<GRAFANA_PASSWORD>" \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
# Optionally add: -e PAGERDUTY_FILTER_USERS="USER1,USER2,USER3" \
oncall-migrator python /app/add_users_to_grafana.py

# Step 4: When ready, run a plan of what will be migrated, including users this time
docker run --rm \
-e MIGRATING_FROM="pagerduty" \
-e MODE="plan" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
oncall-migrator

# Step 4: And finally, when ready, actually migrate your PagerDuty data, again including users
docker run --rm \
-e MIGRATING_FROM="pagerduty" \
-e MODE="migrate" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
oncall-migrator
```

### Resource Filtering

The PagerDuty migrator allows you to filter resources based on team, users, and name patterns.
You can use these filters to limit the scope of your migration.

When multiple filters are applied (e.g., both team and user filters), resources matching **ANY** of the
 filters will be included. This is an OR operation between filter types. For example, if you set:

```bash
-e PAGERDUTY_FILTER_TEAM="DevOps"
-e PAGERDUTY_FILTER_USERS="USER1,USER2"
```

The migrator will include:

- Resources associated with the "DevOps" team
- Resources associated with USER1 or USER2
- Resources that match both criteria

Additionally, when `MIGRATE_USERS` is set to `true` and `PAGERDUTY_FILTER_USERS` is specified,
only the users with the specified PagerDuty IDs will be migrated. This allows for selective user
migration, which is useful when you want to test the migration with a small set of users before
migrating all users.

This allows for more flexible and intuitive filtering when migrating specific subsets of your PagerDuty setup.

### Output Verbosity

By default, the migrator provides a summary of filtered resources without detailed per-resource information.
You can enable verbose logging to see detailed information about each filtered resource:

```bash
docker run --rm \
-e MIGRATING_FROM="pagerduty" \
-e MODE="plan" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
-e PAGERDUTY_VERBOSE_LOGGING="true" \
oncall-migrator
```

This can be helpful for debugging, but otherwise keeping it disabled will significantly reduce output
when dealing with large PagerDuty instances.

### Configuration

Configuration is done via environment variables passed to the docker container.

| Name                                          | Description                                                                                                                                                                                                                                                                                                                                                                                                        | Type                                | Default |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------- | ------- |
| `MIGRATING_FROM`                              | Set to `pagerduty`                                                                                                                                                                                                                                                                                                                                                                                                 | String                              | N/A     |
| `PAGERDUTY_API_TOKEN`                         | PagerDuty API **user token**. To create a token, refer to [PagerDuty docs](https://support.pagerduty.com/docs/api-access-keys#generate-a-user-token-rest-api-key).                                                                                                                                                                                                                                                 | String                              | N/A     |
| `ONCALL_API_URL`                              | Grafana OnCall API URL. This can be found on the "Settings" page of your Grafana OnCall instance.                                                                                                                                                                                                                                                                                                                  | String                              | N/A     |
| `ONCALL_API_TOKEN`                            | Grafana OnCall API Token. To create a token, navigate to the "Settings" page of your Grafana OnCall instance.                                                                                                                                                                                                                                                                                                      | String                              | N/A     |
| `GRAFANA_SERVICE_ACCOUNT_URL`                            | A URL containing your tenant name (e.g. `stacks-xxx`) and Service Account Token. The URL is of the form `https://<stackid>:<token>@<server>`. e.g. `https://stacks-12345:xxxxxx@my-company.grafana.net/` Your stack id can be found at [grafana.com](https://grafana.com)                                                                                                                                                                      .                                                                                                                                | String                              | N/A     |
| `MODE`                                        | Migration mode (plan vs actual migration).                                                                                                                                                                                                                                                                                                                                                                         | String (choices: `plan`, `migrate`) | `plan`  |
| `SCHEDULE_MIGRATION_MODE`                     | Determines how on-call schedules are migrated.                                                                                                                                                                                                                                                                                                                                                                     | String (choices: `ical`, `web`)     | `ical`  |
| `UNSUPPORTED_INTEGRATION_TO_WEBHOOKS`         | When set to `true`, integrations with unsupported type will be migrated to Grafana OnCall integrations with type "webhook". When set to `false`, integrations with unsupported type won't be migrated.                                                                                                                                                                                                             | Boolean                             | `false` |
| `EXPERIMENTAL_MIGRATE_EVENT_RULES`            | Migrate global event rulesets to Grafana OnCall integrations.                                                                                                                                                                                                                                                                                                                                                      | Boolean                             | `false` |
| `EXPERIMENTAL_MIGRATE_EVENT_RULES_LONG_NAMES` | Include service & integrations names from PD in migrated integrations (only effective when `EXPERIMENTAL_MIGRATE_EVENT_RULES` is `true`).                                                                                                                                                                                                                                                                          | Boolean                             | `false` |
| `MIGRATE_USERS`                               | If `false`, will allow you to important all objects, while ignoring user references in schedules and escalation policies. In addition, if `false`, will also skip importing User notification rules. This may be helpful in cases where you are unable to import your list of Grafana users, but would like to experiment with OnCall using your existing PagerDuty setup as a starting point for experimentation. | Boolean                             | `true`  |
| `PAGERDUTY_MIGRATE_SERVICES`                               | If `true`, will allow you to import technical and business services. | Boolean                             | `false`  |
| `PAGERDUTY_FILTER_TEAM`                       | Filter resources by team name. Resources associated with this team will be included in the migration.                                                                                                                                                                                                                                                                                                          | String                              | N/A     |
| `PAGERDUTY_FILTER_USERS`                      | Filter by PagerDuty user IDs (comma-separated). This serves two purposes: 1) Resources associated with any of these users will be included in the migration, and 2) When `MIGRATE_USERS` is `true`, only these specific users will be migrated (not all users).                                                                                                                                                                             | String                              | N/A     |
| `PAGERDUTY_FILTER_SCHEDULE_REGEX`             | Filter schedules by name using a regex pattern. Schedules whose names match this pattern will be included in the migration.                                                                                                                                                                                                                                                                    | String                              | N/A     |
| `PAGERDUTY_FILTER_ESCALATION_POLICY_REGEX`    | Filter escalation policies by name using a regex pattern. Policies whose names match this pattern will be included in the migration.                                                                                                                                                                                                                                                                           | String                              | N/A     |
| `PAGERDUTY_FILTER_INTEGRATION_REGEX`          | Filter integrations by name using a regex pattern. Integrations whose names match this pattern will be included in the migration.                                                                                                                                                                                                                                                                              | String                              | N/A     |
| `PAGERDUTY_FILTER_SERVICE_REGEX`              | Filter services by name using a regex pattern. Only services whose names match this pattern will be migrated. This filter applies to both technical and business services being migrated to Grafana's service model.                                                                                                                                                                                              | String                              | N/A     |
| `PRESERVE_EXISTING_USER_NOTIFICATION_RULES`   | Whether to preserve existing notification rules when migrating users                                                                                                                                                                                                                                                                                                                                               | Boolean                             | `true`  |
| `PAGERDUTY_VERBOSE_LOGGING`                   | Whether to display detailed per-resource information during filtering. When set to `false`, only summary counts will be shown for filtered resources. Use `true` to see why specific resources were filtered out.                                                                                                                                                                                                   | Boolean                             | `false` |

### Resources

#### User notification rules

The tool is capable of migrating user notification rules from PagerDuty to Grafana OnCall.
Notification rules from the `"When a high-urgency incident is assigned to me..."` section in PagerDuty settings are
taken into account and will be migrated to both default and important notification rules in Grafana OnCall
for each user. Note that delays between notification rules may be slightly different in Grafana OnCall,
see [Limitations](#limitations) for more info.

By default (when `PRESERVE_EXISTING_USER_NOTIFICATION_RULES` is `true`), existing notification rules in Grafana OnCall will
be preserved and PagerDuty rules won't be imported for users who already have notification rules configured in Grafana OnCall.

If you want to replace existing notification rules with ones from PagerDuty, set `PRESERVE_EXISTING_USER_NOTIFICATION_RULES`
to `false`.

See [Migrating Users](#migrating-users) for some more information on how users are migrated.

#### On-call schedules

The tool is capable of migrating on-call schedules from PagerDuty to Grafana OnCall.
There are two ways to migrate on-call schedules:

- Migrate on-call shifts as if they were created in Grafana OnCall web UI. Due to scheduling differences between
  PagerDuty and Grafana OnCall, it's sometimes impossible to automatically migrate on-call shifts without manual changes
  in PD. Pass `SCHEDULE_MIGRATION_MODE=web` to the tool to enable this mode.
- Using ICalendar file URLs from PagerDuty. This way it's always possible to migrate schedules without any manual
  changes in PD, but resulting schedules in Grafana OnCall will be read-only. Pass `SCHEDULE_MIGRATION_MODE=ical` to
  the tool to enable this mode.

On-call schedules will be migrated to new Grafana OnCall schedules with the same name as in PD. Any existing schedules
with the same name will be deleted before migration. Any on-call schedules that reference unmatched users won't be
migrated.

When running the plan with `SCHEDULE_MIGRATION_MODE=web`, there could be a number of errors regarding on-call schedules.
These errors are expected and are caused by the fact that the tool can't always automatically migrate on-call shifts
due to differences in scheduling systems in PD and Grafana OnCall. To fix these errors, you need to manually change
on-call shifts in PD and re-run the migration.

#### Escalation policies

The tool is capable of migrating escalation policies from PagerDuty to Grafana OnCall.
Every escalation policy will be migrated to a new Grafana OnCall escalation chain with the same name.

Any existing escalation chains with the same name will be deleted before migration. Any escalation policies that reference
unmatched users or schedules that cannot be migrated won't be migrated as well.

Note that delays between escalation steps may be slightly different in Grafana OnCall,
see [Limitations](#limitations) for more info.

#### Services (integrations)

The tool is capable of migrating services (integrations) from PagerDuty to Grafana OnCall.
For every service in PD, the tool will migrate all integrations to Grafana OnCall integrations.

Any services that reference escalation policies that cannot be migrated won't be migrated as well.
Any integrations with unsupported type won't be migrated unless `UNSUPPORTED_INTEGRATION_TO_WEBHOOKS` is set to `true`.

The following integration types are supported:

- Datadog
- Pingdom
- Prometheus
- PRTG
- Stackdriver
- UptimeRobot
- New Relic
- Zabbix Webhook (for 5.0 and 5.2)
- Elastic Alerts
- Firebase
- Amazon CloudWatch (maps to Amazon SNS integration in Grafana OnCall)

#### Event rules (global event rulesets)

The tool is capable of migrating global event rulesets from PagerDuty to Grafana OnCall integrations. This feature is
experimental and disabled by default. To enable it, set `EXPERIMENTAL_MIGRATE_EVENT_RULES` to `true`.

For every ruleset in PD, the tool will create a webhook integration in Grafana OnCall. The tool will create
a route for every rule in ruleset, converting conditions in PD to Jinja2 routes in Grafana OnCall. The tool will also
select appropriate escalation chains for each route based on service referenced in the rule.

If you want to include service & integration names in the names of migrated integrations, set
`EXPERIMENTAL_MIGRATE_EVENT_RULES_LONG_NAMES` to `true` (note that this only applies when
`EXPERIMENTAL_MIGRATE_EVENT_RULES` is `true`). This can make searching for integrations easier,
but it can also make the names of integrations too long.

#### Services and Business Services

The tool is capable of migrating both technical services and business services from PagerDuty to
Grafana's service model. This feature is disabled by default and can be enabled by setting
`PAGERDUTY_MIGRATE_SERVICES` to `true`.

Set GRAFANA_SERVICE_ACCOUNT_URL to the URL format of a Grafana service account with Admin
permission of the form: `https://<namespace>:<token>@<server>`

When enabled, the tool will:

1. **Technical Services**:
   - Migrate PagerDuty technical services to Grafana Components with type "service"
   - Preserve service metadata and relationships
   - Map escalation policies to appropriate escalation chains
   - Maintain service dependencies and relationships

2. **Business Services**:
   - Migrate PagerDuty business services to Grafana Components with type "business_service"
   - Preserve business service hierarchy and relationships
   - Map technical service dependencies to appropriate Components
   - Maintain business impact relationships

The migration process ensures that:

- Service hierarchies are preserved
- Dependencies between services are maintained
- Escalation policies are properly mapped
- Service metadata and annotations are preserved
- Business impact relationships are maintained

Example:

```bash
docker run --rm \
-e MIGRATING_FROM="pagerduty" \
-e MODE="migrate" \
-e GRAFANA_SERVICE_ACCOUNT_URL="<GRAFANA_SERVICE_ACCOUNT_URL>" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
-e PAGERDUTY_MIGRATE_SERVICES="true" \
oncall-migrator
```

#### Service Filtering

The tool provides several ways to filter which services are migrated:

1. **Team-based filtering** (`PAGERDUTY_FILTER_TEAM`):
   - Only services associated with the specified team will be migrated
   - Applies to both technical and business services

2. **User-based filtering** (`PAGERDUTY_FILTER_USERS`):
   - For technical services: only services with the specified users in their escalation policies will be migrated
   - Business services are not affected by user filters
   - Multiple user IDs can be specified as a comma-separated list

3. **Name-based filtering** (`PAGERDUTY_FILTER_SERVICE_REGEX`):
   - Only services whose names match the specified regex pattern will be migrated
   - Applies to both technical and business services

These filters can be used individually or combined. When multiple filters are applied, a service must match all
active filters to be included in the migration.

Example:

```bash
docker run --rm \
-e MIGRATING_FROM="pagerduty" \
-e MODE="migrate" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
-e PAGERDUTY_FILTER_TEAM="Platform Team" \
-e PAGERDUTY_FILTER_USERS="U123,U456" \
-e PAGERDUTY_FILTER_SERVICE_REGEX="Prod.*" \
oncall-migrator
```

This example will only migrate services that:

- Belong to the "Platform Team"
- Have either user U123 or U456 in their escalation policy (for technical services)
- Have a name starting with "Prod"

### After migration

- Connect integrations (press the "How to connect" button on the integration page)
- Make sure users connect their phone numbers, Slack accounts, etc. in their user settings
- When using `SCHEDULE_MIGRATION_MODE=ical`, at some point you would probably want to recreate schedules using
  Google Calendar or Terraform to be able to modify migrated on-call schedules in Grafana OnCall

## Splunk OnCall

### Overview

Resources that can be migrated using this tool:

- Escalation Policies
- On-Call Schedules (including Rotations + Scheduled Overrides)
<!-- - Teams + team memberships TODO: uncomment out once we support teams-->
- User Paging Policies

### Limitations

- Only the Primary Paging Policy for users are migrated, no Custom Paging Policies are migrated
- Not all Splunk escalation step types are supported
- Delays between migrated notification/escalation rules could be slightly different from original.
  E.g. if you have a 20-minute delay between rules in Splunk OnCall, the resulting delay in Grafana OnCall will be 15 minutes

### Prerequisites

- Obtain your Splunk API ID and an API token: <https://help.victorops.com/knowledge-base/api/#:~:text=currently%20in%20place.-,API%20Configuration%20in%20Splunk%20On%2DCall,-To%20access%20the>

### Configuration

Configuration is done via environment variables passed to the docker container.

| Name               | Description                                                                                                                                                                                                                | Type                                | Default |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- | ------- |
| `MIGRATING_FROM`   | Set to `splunk`                                                                                                                                                                                                            | String                              | N/A     |
| `SPLUNK_API_KEY`   | Splunk API **key**. To create an API Key, refer to [Splunk OnCall docs](https://help.victorops.com/knowledge-base/api/#:~:text=currently%20in%20place.-,API%20Configuration%20in%20Splunk%20On%2DCall,-To%20access%20the). | String                              | N/A     |
| `SPLUNK_API_ID`    | Splunk API **ID**. To retrieve this ID, refer to [Splunk OnCall docs](https://help.victorops.com/knowledge-base/api/#:~:text=currently%20in%20place.-,API%20Configuration%20in%20Splunk%20On%2DCall,-To%20access%20the).   | String                              | N/A     |
| `ONCALL_API_URL`   | Grafana OnCall API URL. This can be found on the "Settings" page of your Grafana OnCall instance.                                                                                                                          | String                              | N/A     |
| `ONCALL_API_TOKEN` | Grafana OnCall API Token. To create a token, navigate to the "Settings" page of your Grafana OnCall instance.                                                                                                              | String                              | N/A     |
| `MODE`             | Migration mode (plan vs actual migration).                                                                                                                                                                                 | String (choices: `plan`, `migrate`) | `plan`  |

### Resources

#### Escalation Policies

The tool is capable of migrating escalation policies from Splunk OnCall to Grafana OnCall.
Every escalation policy will be migrated to a new Grafana OnCall escalation chain with the same name.

Any existing escalation chains with the same name will be deleted before migration. Any escalation policies that reference
unmatched users or schedules that cannot be migrated won't be migrated as well.

##### Caveats

- delays between escalation steps may be slightly different in Grafana OnCall, see [Limitations](#limitations-1) for
  more info.
- the following Splunk OnCall escalation step types are not supported and will not be migrated:
  - "Notify the next user(s) in the current on-duty shift"
  - "Notify the previous user(s) in the current on-duty shift"
  - "Notify every member of this team"
  - "Send an email to email address"
  - "Execute webhook" (as Splunk OnCall webhooks are currently not migrated to Grafana OnCall webhooks)

#### On-call schedules

The tool is capable of migrating on-call schedules from Splunk OnCall to Grafana OnCall. Every Splunk On-Call Schedule
will be migrated to a new Grafana OnCall schedule chain with the name as the Splunk team's name + `schedule`
(ex. `Infra Team schedule`).

Any existing Grafana OnCall schedules with the same name will be deleted before migration.

##### Caveats

We don't currently support multi-day shifts which have a "hand-off" period set to greater than one week.

#### User Paging Policies

The tool is capable of migrating paging policies from Splunk OnCall to Grafana OnCall.
All user's **Primary** paging policy will be migrated to a new Grafana OnCall user notification policy with the same name.

Any existing personal notification policies for these users will be deleted before migration.

See [Migrating Users](#migrating-users) for some more information on how users are migrated.

##### Caveats

- The WhatsApp escalation type is not supported and will not be migrated to the Grafana OnCall
  user's personal notification policy
- Note that delays between escalation steps may be slightly different in Grafana OnCall,
  see [Limitations](#limitations-1) for more info.

## Opsgenie

### Overview

Resources that can be migrated using this tool:

- User notification rules
- On-call schedules (including rotations and overrides)
- Escalation policies
- Integrations

### Limitations

- Not all integration types are supported
- Not all Escalation Policy rule types are supported
- Opsgenie schedules with time restrictions (time-of-day or weekday-and-time-of-day) are not supported
- Delays between migrated notification/escalation rules could be slightly different from original

### Prerequisites

- Obtain an Opsgenie API key: <https://docs.opsgenie.com/docs/api-key-management>

### Configuration

Configuration is done via environment variables passed to the docker container.

| Name                                    | Description                                                                                                                                                                                                                | Type                                | Default |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- | ------- |
| `MIGRATING_FROM`                        | Set to `opsgenie`                                                                                                                                                                                                          | String                              | N/A     |
| `OPSGENIE_API_KEY`                      | Opsgenie API key. To create a key, refer to [Opsgenie docs](https://docs.opsgenie.com/docs/api-key-management).                                                                                                            | String                              | N/A     |
| `OPSGENIE_API_URL`                      | Opsgenie API URL. Use `https://api.eu.opsgenie.com/v2` for EU instances.                                                                                                                                                  | String                              | `https://api.opsgenie.com/v2` |
| `ONCALL_API_URL`                        | Grafana OnCall API URL. This can be found on the "Settings" page of your Grafana OnCall instance.                                                                                                                          | String                              | N/A     |
| `ONCALL_API_TOKEN`                      | Grafana OnCall API Token. To create a token, navigate to the "Settings" page of your Grafana OnCall instance.                                                                                                              | String                              | N/A     |
| `MODE`                                  | Migration mode (plan vs actual migration).                                                                                                                                                                                 | String (choices: `plan`, `migrate`) | `plan`  |
| `UNSUPPORTED_INTEGRATION_TO_WEBHOOKS`   | When set to `true`, integrations with unsupported type will be migrated to Grafana OnCall integrations with type "webhook". When set to `false`, integrations with unsupported type won't be migrated.                    | Boolean                             | `false` |
| `MIGRATE_USERS`                         | If `false`, will allow you to import all objects while ignoring user references in schedules and escalation policies. In addition, if `false`, will also skip importing User notification rules.                            | Boolean                             | `true`  |
| `OPSGENIE_FILTER_TEAM`                  | Filter resources by team name. Only resources associated with this team will be migrated.                                                                                                                                  | String                              | N/A     |
| `OPSGENIE_FILTER_USERS`                 | Filter resources by Opsgenie user IDs (comma-separated). Only resources associated with these users will be migrated.                                                                                                      | String                              | N/A     |
| `OPSGENIE_FILTER_SCHEDULE_REGEX`        | Filter schedules by name using a regex pattern. Only schedules whose names match this pattern will be migrated.                                                                                                            | String                              | N/A     |
| `OPSGENIE_FILTER_ESCALATION_POLICY_REGEX` | Filter escalation policies by name using a regex pattern. Only policies whose names match this pattern will be migrated.                                                                                                   | String                              | N/A     |
| `OPSGENIE_FILTER_INTEGRATION_REGEX`     | Filter integrations by name using a regex pattern. Only integrations whose names match this pattern will be migrated.                                                                                                      | String                              | N/A     |
| `PRESERVE_EXISTING_USER_NOTIFICATION_RULES` | Whether to preserve existing notification rules when migrating users                                                                                                                                                      | Boolean                             | `true`  |

### Resources

#### User notification rules

The tool is capable of migrating user notification rules from Opsgenie to Grafana OnCall.
Notification rules from Opsgenie will be migrated to both default and important notification rules in Grafana OnCall
for each user. Note that delays between notification rules may be slightly different in Grafana OnCall.

By default (when `PRESERVE_EXISTING_USER_NOTIFICATION_RULES` is `true`), existing notification rules in Grafana OnCall will
be preserved and Opsgenie rules won't be imported for users who already have notification rules configured in Grafana OnCall.

If you want to replace existing notification rules with ones from Opsgenie, set `PRESERVE_EXISTING_USER_NOTIFICATION_RULES`
to `false`.

See [Migrating Users](#migrating-users) for some more information on how users are migrated.

#### On-call schedules

The tool is capable of migrating on-call schedules from Opsgenie to Grafana OnCall.
Schedules are migrated with their rotations. The following features are supported:

- Daily, weekly, and hourly rotations
- Multiple rotations per schedule
- Schedule overrides

On-call schedules will be migrated to new Grafana OnCall schedules with the same name as in Opsgenie.
Any existing schedules with the same name will be deleted before migration.
Any on-call schedules that reference unmatched users won't be migrated. Any Opsgenie schedule which
uses time restrictions will not be migrated as migrating these is not supported.

#### Escalation policies

The tool is capable of migrating escalation policies from Opsgenie to Grafana OnCall.
Every escalation policy will be migrated to a new Grafana OnCall escalation chain with name convention of
`{team name} - {escalation policy name}`.

Caveats:

- Only the "Notify user" and "Notify on-call user(s) in schedule" rule types are supported. If an Opsgenie Escalation
Policy references a rule other than these, those rule steps are simply ignored in the migration
- Any existing escalation chains with the same name will be deleted, in Grafana OnCall, before migration.
Note that delays between escalation steps may be slightly different in Grafana OnCall
- Grafana OnCall Escalation Policies which are migrated, are not attached to any Integration/Route, and must
be done manually

#### Integrations

The tool is capable of migrating integrations from Opsgenie to Grafana OnCall.
For every integration in Opsgenie, the tool will migrate it to a Grafana OnCall integration.

Any integrations with unsupported type won't be migrated unless `UNSUPPORTED_INTEGRATION_TO_WEBHOOKS` is set to `true`.

The following integration types are supported:

- Amazon CloudWatch (maps to Amazon SNS integration in Grafana OnCall)
- Amazon SNS
- AppDynamics
- Datadog
- Email
- Jira (including Jira Service Desk)
- Kapacitor
- New Relic (including legacy New Relic)
- Pingdom (including Pingdom Server Monitor (Scout))
- Prometheus (maps to Alertmanager in Grafana OnCall)
- PRTG
- Sentry
- Stackdriver
- UptimeRobot
- Webhook
- Zabbix

### After migration

- Connect integrations (press the "How to connect" button on the integration page)
- Make sure users connect their phone numbers, Slack accounts, etc. in their user settings
- Review and adjust any webhook integrations that were migrated from unsupported Opsgenie integration types

## Migrating Users

Note that users are matched by email, so if there are users in the report with "no Grafana OnCall user found with
this email" error, it's possible to fix it by adding these users to your Grafana organization.

If there are a large number of unmatched users, you can use the following script that will automatically create missing
Grafana users via the Grafana HTTP API.

**NOTE**: The script will create users with random passwords, so they will need to reset their passwords later in Grafana.

### PagerDuty

```bash
docker run --rm \
-e MIGRATING_FROM="pagerduty" \
-e GRAFANA_URL="<GRAFANA_API_URL>" \
-e GRAFANA_USERNAME="<GRAFANA_USERNAME>" \
-e GRAFANA_PASSWORD="<GRAFANA_PASSWORD>" \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
oncall-migrator python /app/add_users_to_grafana.py
```

You can also filter which PagerDuty users are added to Grafana by using the `PAGERDUTY_FILTER_USERS` environment variable:

```bash
docker run --rm \
-e MIGRATING_FROM="pagerduty" \
-e GRAFANA_URL="<GRAFANA_API_URL>" \
-e GRAFANA_USERNAME="<GRAFANA_USERNAME>" \
-e GRAFANA_PASSWORD="<GRAFANA_PASSWORD>" \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
-e PAGERDUTY_FILTER_USERS="PD_USER_ID_1,PD_USER_ID_2,PD_USER_ID_3" \
oncall-migrator python /app/add_users_to_grafana.py
```

This is useful when you want to selectively add users to Grafana, such as when testing the migration process
or when you only need to add specific users from a large PagerDuty organization.
The `PAGERDUTY_FILTER_USERS` variable should contain a comma-separated list of PagerDuty user IDs.

### Splunk OnCall (VictorOps)

```bash
docker run --rm \
-e MIGRATING_FROM="splunk" \
-e GRAFANA_URL="<GRAFANA_API_URL>" \
-e GRAFANA_USERNAME="<GRAFANA_USERNAME>" \
-e GRAFANA_PASSWORD="<GRAFANA_PASSWORD>" \
-e SPLUNK_API_ID="<SPLUNK_API_ID>" \
-e SPLUNK_API_KEY="<SPLUNK_API_KEY>" \
oncall-migrator python /app/add_users_to_grafana.py
```

### Opsgenie

```bash
docker run --rm \
-e MIGRATING_FROM="opsgenie" \
-e GRAFANA_URL="<GRAFANA_API_URL>" \
-e GRAFANA_USERNAME="<GRAFANA_USERNAME>" \
-e GRAFANA_PASSWORD="<GRAFANA_PASSWORD>" \
-e OPSGENIE_API_KEY="<OPSGENIE_API_KEY>" \
-e OPSGENIE_API_URL="<OPSGENIE_API_URL>" \
oncall-migrator python /app/add_users_to_grafana.py
```

You can also filter which Opsgenie users are added to Grafana by using the `OPSGENIE_FILTER_USERS` environment variable:

```bash
docker run --rm \
-e MIGRATING_FROM="opsgenie" \
-e GRAFANA_URL="<GRAFANA_API_URL>" \
-e GRAFANA_USERNAME="<GRAFANA_USERNAME>" \
-e GRAFANA_PASSWORD="<GRAFANA_PASSWORD>" \
-e OPSGENIE_API_KEY="<OPSGENIE_API_KEY>" \
-e OPSGENIE_API_URL="<OPSGENIE_API_URL>" \
-e OPSGENIE_FILTER_USERS="OPSGENIE_USER_ID_1,OPSGENIE_USER_ID_2,OPSGENIE_USER_ID_3" \
oncall-migrator python /app/add_users_to_grafana.py
```

This is useful when you want to selectively add users to Grafana, such as when testing the migration process
or when you only need to add specific users from a large Opsgenie organization.
The `OPSGENIE_FILTER_USERS` variable should contain a comma-separated list of Opsgenie user IDs.
