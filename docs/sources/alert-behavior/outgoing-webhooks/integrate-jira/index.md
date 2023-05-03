---
aliases:
  - ../integrations/configure-outgoing-webhooks/integrate-jira/
  - /docs/oncall/latest/alert-behavior/outgoing-webhooks/integrate-jira/
canonical: https://grafana.com/docs/oncall/latest/alert-behavior/outgoing-webhooks/integrate-jira/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - amixr
  - webhooks
  - Jira
title: Integrate Grafana OnCall with Jira
weight: 300
---

# Integrate Grafana OnCall with Jira

Grafana OnCall can automatically create and resolve issues in Jira via [outgoing webhooks]({{< relref "_index.md" >}}).
This guide provides example webhook configurations for common use cases, as well as information on how to set up a user in Jira to be used by Grafana OnCall.

## Prerequisites

1. Create a new user in Jira to be used by Grafana OnCall. [Obtain an API token for the user](https://id.atlassian.com/manage-profile/security/api-tokens),
these credentials will be used to communicate with Jira REST API.
2. Make sure the user has appropriate permissions to create and update issues in Jira.

## Create issues in Jira

The steps below describe how to create an outgoing webhook in Grafana OnCall that will allow to automatically create
issues in Jira from Grafana OnCall alert groups.

Create a new Outgoing Webhook in Grafana OnCall, and configure it as follows:

- Trigger type: `Alert Group Created`

- Integrations: Select integrations that will trigger the webhook

- HTTP method: `POST`

- Webhook URL:

```text
https://<INSTANCE>.atlassian.net/rest/api/2/issue
```

Replace `<INSTANCE>` with your Jira instance.

- Username: Email of the [Jira user](#prerequisites)

- Password: API token of the [Jira user](#prerequisites)

Use the following JSON template as webhook data:

```json
{
  "fields": {
    "project": {
      "key": "<PROJECT_KEY>"
    },
    "issuetype": {
      "name": "[System] Incident"
    },
    "summary": "{{alert_group.title}}",
    "description": "This issue is created automatically by Grafana OnCall. Alert group {{alert_group.id}}: {{alert_group.permalinks.web}}"
  }
}
```

Replace `<PROJECT_KEY>` with the key of the project in Jira.

>**Note**: You might want to use a different `issuetype.name` depending on your Jira instance configuration and use case.

## Resolve issues in Jira

The steps below describe how to create an outgoing webhook in Grafana OnCall that will allow to automatically resolve
issues in Jira when an alert group is resolved in Grafana OnCall.

- Trigger type: `Resolved`

- Integrations: Select integrations that will trigger the webhook

- HTTP method: `POST`

- Webhook URL:

```text
https://<INSTANCE>.atlassian.net/rest/api/2/issue/{{responses.<WEBHOOK_ID>.key}}/transitions
```

Replace `<INSTANCE>` with your Jira instance, and `<WEBHOOK_ID>` with the ID of the [webhook used for creating issues](#create-issues-in-jira).

- Username: Email of the [Jira user](#prerequisites)

- Password: API token of the [Jira user](#prerequisites)

Use the following JSON template as webhook data:

```json
{
  "transition": {
    "id": "<TRANSITION_ID>"
  },
  "fields": {
    "resolution": {
      "name": "Done"
    }
  },
  "update": {
    "comment": [
      {
        "add": {
          "body": "Resolved by Grafana OnCall.",
          "public": false
        }
      }
    ]
  }
}
```

Replace `<TRANSITION_ID>` with the ID of the transition specific to your Jira instance.
See [here](https://community.atlassian.com/t5/Jira-questions/How-to-fine-transition-ID-of-JIRA/qaq-p/1207483#M385834)
for more info on how to find the transition ID in Jira UI, or use the
[REST API endpoint](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-transitions-get)
to get the list of available transitions.

## Advanced usage

The examples above describe how to create outgoing webhooks in Grafana OnCall that will allow to automatically create and resolve issues in Jira.

Consider modifying example templates to fit your use case (e.g. to include more information on alert groups).
Refer to [outgoing webhooks documentation]({{< relref "_index.md" >}}) for more information on available template variables and webhook configuration.

For more information on Jira REST API, refer to [Jira REST API documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issues).
