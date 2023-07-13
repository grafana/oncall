---
aliases:
  - jira/
  - /docs/oncall/latest/integrations/available-integrations/configure-jira/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-jira/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - webhooks
  - Jira
title: Jira
weight: 500
---

# Jira integration for Grafana OnCall

The Jira integration for Grafana OnCall handles issue events sent from Jira webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin][user-and-team-management] to be able to create integrations in Grafana OnCall.

## Configuring Grafana OnCall to Receive Alerts from Jira

1. In the **Integrations** tab, click **+ New integration**.
2. Select **Jira** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section. You will need it when configuring Jira.

## Configuring Jira to Send Alerts to Grafana OnCall

Create a new webhook connection in Jira to send events to Grafana OnCall using the integration URL above.

Refer to [Jira documentation](https://developer.atlassian.com/server/jira/platform/webhooks/) for more information on how to create and manage webhooks

When creating a webhook in Jira, select the following events to be sent to Grafana OnCall:

1. Issue - created
2. Issue - updated
3. Issue - deleted
After setting up the connection, you can test it by creating a new issue in Jira. You should see a new alert group in Grafana OnCall.

## Grouping, auto-acknowledge and auto-resolve

Grafana OnCall provides grouping, auto-acknowledge and auto-resolve logic for the Jira integration:

- Alerts created from issue events are grouped by issue key
- Alert groups are auto-acknowledged when the issue status is set to "work in progress"
- Alert groups are auto-resolved when the issue is closed or deleted

To customize this behaviour, consider modifying alert templates in integration settings.

## Configuring Grafana OnCall to send data to Jira

Grafana OnCall can automatically create and resolve issues in Jira via [outgoing webhooks]({{< relref "_index.md" >}}).
This guide provides example webhook configurations for common use cases, as well as information on how to set up a user in Jira to be used by Grafana OnCall.

### Prerequisites

1. Create a new user in Jira to be used by Grafana OnCall. [Obtain an API token for the user](https://id.atlassian.com/manage-profile/security/api-tokens),
these credentials will be used to communicate with Jira REST API.
2. Make sure the user has appropriate permissions to create and update issues in Jira.

### Create issues in Jira

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

### Resolve issues in Jira

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

### Advanced usage

The examples above describe how to create outgoing webhooks in Grafana OnCall that will allow to automatically create and resolve issues in Jira.

Consider modifying example templates to fit your use case (e.g. to include more information on alert groups).
Refer to [outgoing webhooks documentation]({{< relref "_index.md" >}}) for more information on available template variables and webhook configuration.

For more information on Jira REST API, refer to [Jira REST API documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issues).

{{% docs/reference %}}
[user-and-team-management]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
[user-and-team-management]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/user-and-team-management"
{{% /docs/reference %}}
