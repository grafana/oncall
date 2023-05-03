---
aliases:
  - ../integrations/configure-outgoing-webhooks/integrate-zendesk/
  - /docs/oncall/latest/alert-behavior/outgoing-webhooks/integrate-zendesk/
canonical: https://grafana.com/docs/oncall/latest/alert-behavior/outgoing-webhooks/integrate-zendesk/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - amixr
  - webhooks
  - Zendesk
title: Integrate Grafana OnCall with Zendesk
weight: 300
---

# Integrate Grafana OnCall with Zendesk

Grafana OnCall can automatically create and resolve tickets in Zendesk via [outgoing webhooks]({{< relref "_index.md" >}}).
This guide provides example webhook configurations for common use cases, as well as information on how to set up a user in Zendesk to be used by Grafana OnCall.

## Prerequisites

1. Create a new user in Zendesk to be used by Grafana OnCall.
[Obtain an API token for the user](https://support.zendesk.com/hc/en-us/articles/4408889192858-Generating-a-new-API-token),
these credentials will be used to communicate with Zendesk API.
2. Make sure the user has appropriate permissions to create and update tickets in Zendesk.

## Create tickets in Zendesk

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

## Resolve tickets in Zendesk

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

## Advanced usage

The examples above describe how to create outgoing webhooks in Grafana OnCall that will allow to automatically create and resolve tickets in Zendesk.

Consider modifying example templates to fit your use case (e.g. to include more information on alert groups).
Refer to [outgoing webhooks documentation]({{< relref "_index.md" >}}) for more information on available template variables and webhook configuration.

For more information on Zendesk API, refer to [Zendesk API documentation](https://developer.zendesk.com/api-reference/ticketing/tickets/tickets/).
