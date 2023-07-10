---
aliases:
  - servicenow/
  - /docs/oncall/latest/integrations/available-integrations/configure-servicenow/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-servicenow/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - webhooks
  - ServiceNow
title: ServiceNow
weight: 500
---

# Integrate Grafana OnCall with ServiceNow

Grafana OnCall can automatically create, assign and resolve incidents in ServiceNow via [outgoing webhooks]({{< relref "_index.md" >}}).
This guide provides example webhook configurations for common use cases, as well as information on how to set up a user in ServiceNow to be used by Grafana OnCall.

## Prerequisites

1. Create a new user in ServiceNow to be used by Grafana OnCall. Obtain the username and password for the user,
these credentials will be used to communicate with ServiceNow REST API.
2. Make sure the user has appropriate permissions to create and update incidents in ServiceNow. By default, the user will need to have the `sn_incident_write` role.

## Create incidents in ServiceNow

The steps below describe how to create an outgoing webhook in Grafana OnCall that will allow to automatically create
incidents in ServiceNow from Grafana OnCall alert groups.

Create a new Outgoing Webhook in Grafana OnCall, and configure it as follows:

- Trigger type: `Alert Group Created`

- Integrations: Select integrations that will trigger the webhook

- HTTP method: `POST`

- Webhook URL:

```text
https://<INSTANCE>.service-now.com/api/now/table/incident
```

Replace `<INSTANCE>` with your ServiceNow instance.

- Username: Username of the [ServiceNow user](#prerequisites)

- Password: Password of the [ServiceNow user](#prerequisites)

Use the following JSON template as webhook data:

```json
{
  "short_description": "{{alert_group.title}}",
  "description": "This incident is created automatically by Grafana OnCall.",
  "work_notes": "Grafana OnCall alert group: [code]<a target='_blank' href='{{alert_group.permalinks.web}}'>{{alert_group.id}}</a>[/code]",
  "category": "Software"
}
```

## Assign incidents in ServiceNow

The steps below describe how to create an outgoing webhook in Grafana OnCall that will allow to automatically assign incidents in ServiceNow.
The assignment will be performed when an alert group is acknowledged in Grafana OnCall.

- Trigger type: `Acknowledged`

- Integrations: Select integrations that will trigger the webhook

- HTTP method: `PUT`

- Webhook URL:

```text
https://<INSTANCE>.service-now.com/api/now/table/incident/{{responses.<WEBHOOK_ID>.result.sys_id}}
```

Replace `<INSTANCE>` with your ServiceNow instance, and `<WEBHOOK_ID>` with the ID of the [webhook used for creating incidents](#create-incidents-in-servicenow).

- Username: Username of the [ServiceNow user](#prerequisites)

- Password: Password of the [ServiceNow user](#prerequisites)

Use the following JSON template as webhook data:

```json
{
  "assigned_to": "{{user.email}}"
}
```

>**Note**: The incident will be assigned to the user that acknowledged the alert group in Grafana OnCall.
The assignment will fail if the user email does not exist in ServiceNow.

## Resolve incidents in ServiceNow

The steps below describe how to create an outgoing webhook in Grafana OnCall that will allow to automatically close
incidents in ServiceNow when an alert group is resolved in Grafana OnCall.

- Trigger type: `Resolved`

- Integrations: Select integrations that will trigger the webhook

- HTTP method: `PUT`

- Webhook URL:

```text
https://<INSTANCE>.service-now.com/api/now/table/incident/{{responses.<WEBHOOK_ID>.result.sys_id}}
```

Replace `<INSTANCE>` with your ServiceNow instance, and `<WEBHOOK_ID>` with the ID of the [webhook used for creating incidents](#create-incidents-in-servicenow).

- Username: Username of the [ServiceNow user](#prerequisites)

- Password: Password of the [ServiceNow user](#prerequisites)

Use the following JSON template as webhook data:

```json
{
  "state": 6,  
  "close_code": "Resolved by caller",
  "close_notes": "Resolved by Grafana OnCall."
}
```

>**Note**: Values for fields `state` and `close_code` may be different for your ServiceNow instance, please check and update the values accordingly.

## Advanced usage

The examples above describe how to create outgoing webhooks in Grafana OnCall that will allow to automatically create, assign and resolve incidents in ServiceNow.

Consider modifying example templates to fit your use case (e.g. to include more information on alert groups).
Refer to [outgoing webhooks documentation]({{< relref "_index.md" >}}) for more information on available template variables and webhook configuration.

For more information on ServiceNow REST API, refer to [ServiceNow REST API documentation](https://developer.servicenow.com/dev.do#!/reference/api/sandiego/rest).
