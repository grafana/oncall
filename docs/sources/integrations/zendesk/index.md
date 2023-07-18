---
aliases:
  - add-zendesk/
  - /docs/oncall/latest/integrations/available-integrations/configure-zendesk/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-zendesk/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - webhooks
  - Zendesk
title: Zendesk
weight: 500
---

# Zendesk integration for Grafana OnCall

The Zendesk integration for Grafana OnCall handles ticket events sent from Zendesk webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin][user-and-team-management] to be able to create integrations in Grafana OnCall.

## Configuring Grafana OnCall to Receive Alerts from Zendesk

1. In the **Integrations** tab, click **+ New integration**.
2. Select **Zendesk** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.

## Configuring Zendesk to Send Alerts to Grafana OnCall

Create a new "Trigger or automation" webhook connection in Zendesk to send events to Grafana OnCall using the integration URL above.

Refer to [Zendesk documentation](<https://support.zendesk.com/hc/en-us/articles/4408839108378-Creating-webhooks-to-interact-with-third-party-systems>)
for more information on how to create and manage webhooks.

After setting up a webhook in Zendesk, create a new trigger with the following condition:
`Meet ANY of the following conditions: "Ticket Is Created", "Ticket status Changed"`

Set `Notify webhook` as the trigger action and select the webhook you created earlier.
In the JSON body field, use the following JSON template:

```json
{
  "ticket": {
    "id": "{{ticket.id}}",
    "url": "{{ticket.url}}",
    "status": "{{ticket.status}}",
    "title": "{{ticket.title}}",
    "description": "{{ticket.description}}"
  }
}
```

After setting up the connection, you can test it by creating a new ticket in Zendesk. You should see a new alert group in Grafana OnCall.

## Grouping, auto-acknowledge and auto-resolve

Grafana OnCall provides grouping, auto-acknowledge and auto-resolve logic for the Zendesk integration:

- Alerts created from ticket events are grouped by ticket ID
- Alert groups are auto-acknowledged when the ticket status is set to "Pending"
- Alert groups are auto-resolved when the ticket status is set to "Solved"

To customize this behaviour, consider modifying alert templates in integration settings.

## Configuring Grafana OnCall to send data to Zendesk

Grafana OnCall can automatically create and resolve tickets in Zendesk via [outgoing webhooks][outgoing-webhooks].
This guide provides example webhook configurations for common use cases, as well as information on how to set up a user in Zendesk to be used by Grafana OnCall.

### Prerequisites

1. Create a new user in Zendesk to be used by Grafana OnCall.
[Obtain an API token for the user](https://support.zendesk.com/hc/en-us/articles/4408889192858-Generating-a-new-API-token),
these credentials will be used to communicate with Zendesk API.
2. Make sure the user has appropriate permissions to create and update tickets in Zendesk.

### Create tickets in Zendesk

The steps below describe how to create an outgoing webhook in Grafana OnCall that will allow to automatically create
tickets in Zendesk from Grafana OnCall alert groups.

Create a new Outgoing Webhook in Grafana OnCall, and configure it as follows:

- Trigger type: `Alert Group Created`

- Integrations: Select integrations that will trigger the webhook

- HTTP method: `POST`

- Webhook URL:

```text
https://<INSTANCE>.zendesk.com/api/v2/tickets
```

Replace `<INSTANCE>` with your Zendesk instance.

- Username: Username of the [Zendesk user](#prerequisites), followed by `/token` (e.g. `user@example.com/token`)

- Password: API token of the [Zendesk user](#prerequisites)

Use the following JSON template as webhook data:

```json
{
  "ticket": {
    "type": "incident",
    "subject": "{{alert_group.title}}",
    "comment": {
      "body": "This ticket is created automatically by Grafana OnCall. Alert group {{alert_group.id}}: {{alert_group.permalinks.web}}"
    }
  }
}
```

### Resolve tickets in Zendesk

The steps below describe how to create an outgoing webhook in Grafana OnCall that will allow to automatically resolve
tickets in Zendesk when an alert group is resolved in Grafana OnCall.

- Trigger type: `Resolved`

- Integrations: Select integrations that will trigger the webhook

- HTTP method: `PUT`

- Webhook URL:

```text
https://<INSTANCE>.zendesk.com/api/v2/tickets/{{responses.<WEBHOOK_ID>.ticket.id}}
```

Replace `<INSTANCE>` with your Zendesk instance, and `<WEBHOOK_ID>` with the ID of the [webhook used for creating tickets](#create-tickets-in-zendesk).

- Username: Username of the [Zendesk user](#prerequisites), followed by `/token` (e.g. `user@example.com/token`)

- Password: API token of the [Zendesk user](#prerequisites)

Use the following JSON template as webhook data:

```json
{
  "ticket": {
    "status": "solved",
    "comment": {
      "body": "Resolved by Grafana OnCall.",
      "public": false
    }
  }
}
```

### Advanced usage

The examples above describe how to create outgoing webhooks in Grafana OnCall that will allow to automatically create and resolve tickets in Zendesk.

Consider modifying example templates to fit your use case (e.g. to include more information on alert groups).
Refer to [outgoing webhooks documentation][outgoing-webhooks] for more information on available template variables and webhook configuration.

For more information on Zendesk API, refer to [Zendesk API documentation](https://developer.zendesk.com/api-reference/ticketing/tickets/tickets/).

{{% docs/reference %}}
[user-and-team-management]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
[user-and-team-management]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/user-and-team-management"
{{% /docs/reference %}}
