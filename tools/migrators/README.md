# Grafana OnCall migrator tools

These tools will help you to migrate from various on-call tools to Grafana OnCall.

Currently the migration tool supports migrating from:

- PagerDuty
- Splunk OnCall (VictorOps)

## Getting Started

1. Make sure you have `docker` installed and running
2. Build the docker image: `docker build -t oncall-migrator .`
3. Obtain a Grafana OnCall API token and API URL on the "Settings" page of your Grafana OnCall instance
4. Depending on which tool you are migrating from, see more specific instructions there:
    - [PagerDuty](#prerequisites)
    - [Splunk OnCall](#prerequisites-1)
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

Please read the generated report carefully since depending on the content of the report, some  resources
could be not migrated and some existing Grafana OnCall resources could be deleted.

```text
User notification rules report:
    ✅ John Doe (john.doe@example.com) (existing notification rules will be deleted)
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

### Configuration

Configuration is done via environment variables passed to the docker container.

| Name                                          | Description                                                                                                                                                                                            | Type                                | Default |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------- | ------- |
| `MIGRATING_FROM`                         | Set to `pagerduty`                                     | String                              | N/A     |
| `PAGERDUTY_API_TOKEN`                         | PagerDuty API **user token**. To create a token, refer to [PagerDuty docs](https://support.pagerduty.com/docs/api-access-keys#generate-a-user-token-rest-api-key).                                     | String                              | N/A     |
| `ONCALL_API_URL`                              | Grafana OnCall API URL. This can be found on the "Settings" page of your Grafana OnCall instance.                                                                                                      | String                              | N/A     |
| `ONCALL_API_TOKEN`                            | Grafana OnCall API Token. To create a token, navigate to the "Settings" page of your Grafana OnCall instance.                                                                                          | String                              | N/A     |
| `MODE`                                        | Migration mode (plan vs actual migration).                                                                                                                                                             | String (choices: `plan`, `migrate`) | `plan`  |
| `SCHEDULE_MIGRATION_MODE`                     | Determines how on-call schedules are migrated.                                                                                                                                                         | String (choices: `ical`, `web`)     | `ical`  |
| `UNSUPPORTED_INTEGRATION_TO_WEBHOOKS`         | When set to `true`, integrations with unsupported type will be migrated to Grafana OnCall integrations with type "webhook". When set to `false`, integrations with unsupported type won't be migrated. | Boolean                             | `false` |
| `EXPERIMENTAL_MIGRATE_EVENT_RULES`            | Migrate global event rulesets to Grafana OnCall integrations.                                                                                                                                          | Boolean                             | `false` |
| `EXPERIMENTAL_MIGRATE_EVENT_RULES_LONG_NAMES` | Include service & integrations names from PD in migrated integrations (only effective when `EXPERIMENTAL_MIGRATE_EVENT_RULES` is `true`).                                                              | Boolean                             | `false` |

### Resources

#### User notification rules

The tool is capable of migrating user notification rules from PagerDuty to Grafana OnCall.
Notification rules from the `"When a high-urgency incident is assigned to me..."` section in PagerDuty settings are
taken into account and will be migrated to default notification rules in Grafana OnCall for each user. Note that delays
between notification rules may be slightly different in Grafana OnCall, see [Limitations](#limitations) for more info.

When running the migration, existing notification rules in Grafana OnCall will be deleted for every affected user.

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
- Teams + team memberships
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

| Name                                          | Description                                                                                                                                                                                            | Type                                | Default |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------- | ------- |
| `MIGRATING_FROM`                         | Set to `splunk`                                     | String                              | N/A     |
| `SPLUNK_API_KEY`                         | Splunk API **key**. To create an API Key, refer to [Splunk OnCall docs](https://help.victorops.com/knowledge-base/api/#:~:text=currently%20in%20place.-,API%20Configuration%20in%20Splunk%20On%2DCall,-To%20access%20the).                                     | String                              | N/A     |
| `SPLUNK_API_ID`                         | Splunk API **ID**. To retrieve this ID, refer to [Splunk OnCall docs](https://help.victorops.com/knowledge-base/api/#:~:text=currently%20in%20place.-,API%20Configuration%20in%20Splunk%20On%2DCall,-To%20access%20the).                                     | String                              | N/A     |
| `ONCALL_API_URL`                              | Grafana OnCall API URL. This can be found on the "Settings" page of your Grafana OnCall instance.                                                                                                      | String                              | N/A     |
| `ONCALL_API_TOKEN`                            | Grafana OnCall API Token. To create a token, navigate to the "Settings" page of your Grafana OnCall instance.                                                                                          | String                              | N/A     |
| `MODE`                                        | Migration mode (plan vs actual migration).                                                                                                                                                             | String (choices: `plan`, `migrate`) | `plan`  |

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
-e GRAFANA_URL="http://localhost:3000" \
-e GRAFANA_USERNAME="admin" \
-e GRAFANA_PASSWORD="admin" \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
oncall-migrator python /app/add_users_to_grafana.py
```

### Splunk OnCall (VictorOps)

```bash
docker run --rm \
-e MIGRATING_FROM="splunk" \
-e GRAFANA_URL="http://localhost:3000" \
-e GRAFANA_USERNAME="admin" \
-e GRAFANA_PASSWORD="admin" \
-e SPLUNK_API_ID="<SPLUNK_API_ID>" \
-e SPLUNK_API_KEY="<SPLUNK_API_KEY>" \
oncall-migrator python /app/add_users_to_grafana.py
```
