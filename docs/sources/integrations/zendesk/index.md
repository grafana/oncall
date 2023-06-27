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
  - Zendesk
title: Zendesk
weight: 500
---

# Zendesk integration for Grafana OnCall

The Zendesk integration for Grafana OnCall handles ticket events sent from Zendesk webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin]({{< relref "user-and-team-management" >}}) to be able to create integrations in Grafana OnCall.

## Configuring Grafana OnCall to Receive Alerts from Zendesk

1. In the **Integrations** tab, click **+ New integration**.
2. Select **Zendesk** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.

## Configuring Zendesk to Send Alerts to Grafana OnCall

Create a new "Trigger or automation" webhook connection in Zendesk to send events to Grafana OnCall using the integration URL above.

Refer to [Zendesk documentation]
(<https://support.zendesk.com/hc/en-us/articles/4408839108378-Creating-webhooks-to-interact-with-third-party-systems>
) for more information on how to create and manage webhooks.

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
