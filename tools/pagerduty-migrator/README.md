# PagerDuty to Grafana OnCall migrator tool

This tool helps to migrate PagerDuty configuration to Grafana OnCall.

Resources that can be migrated using this tool:

- User notification rules
- Escalation policies
- On-call schedules
- Integrations (services)

## Limitations

- Not all integration types are supported
- Migrated on-call schedules in Grafana OnCall will use ICalendar files from PagerDuty
- Delays between migrated notification/escalation rules could be slightly different from original.
  E.g. if you have a 4-minute delay between rules in PagerDuty, the resulting delay in Grafana OnCall will be 5 minutes

## Prerequisites

1. Make sure you have `docker` installed
2. Build the docker image: `docker build -t pd-oncall-migrator .`
3. Obtain a PagerDuty API user token: <https://support.pagerduty.com/docs/api-access-keys#generate-a-user-token-rest-api-key>
4. Obtain a Grafana OnCall API token and API URL on the "Settings" page of your Grafana OnCall instance

## Migration plan

Before starting the migration process, it's useful to see a migration plan by running the tool in `plan` mode:

```shell
docker run --rm \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e MODE="plan" \
pd-oncall-migrator
```

Please read the generated report carefully since depending on the content of the report, some PagerDuty resources
could not be migrated and some existing Grafana OnCall resources could be deleted.

Note that users are matched by email, so if there are users in the report with "no Grafana OnCall user found with
this email" error, it's possible to fix it by adding these users to your Grafana organization.
If there is a large number of unmatched users, please also [see the script](scripts/README.md) that can automatically
create missing Grafana users via Grafana HTTP API.

### Example migration plan

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

## Migration

Once you are happy with the migration report, start the migration by setting the `MODE` environment variable to `migrate`:

```shell
docker run --rm \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
-e ONCALL_API_URL="<ONCALL_API_URL>" \
-e ONCALL_API_TOKEN="<ONCALL_API_TOKEN>" \
-e ONCALL_DEFAULT_CONTACT_METHOD="sms" \
-e MODE="migrate" \
pd-oncall-migrator
```

It's possible to specify a default contact method type for user notification rules that cannot be migrated as-is by
changing the `ONCALL_DEFAULT_CONTACT_METHOD` env variable.
Options are: `email`, `sms`, `phone_call`, `slack`, `telegram`, `mobile_app` (default is `email`).

### After migration

- Connect integrations (press the "How to connect" button on the integration page)
- Make sure users connect their phone numbers, Slack accounts, etc. in their user settings
- At some point you would probably want to recreate schedules using Google Calendar or Terraform to be able to modify
  migrated on-call schedules in Grafana OnCall
