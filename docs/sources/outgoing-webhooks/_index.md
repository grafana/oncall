---
canonical: https://grafana.com/docs/oncall/latest/outgoing-webhooks/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - amixr
  - webhooks
title: Outgoing Webhooks
weight: 500
---

# Outgoing Webhooks

> ⚠️ A note about **(Legacy)** webhooks: Webhooks that were created before version **v1.3.11** are marked as
> **(Legacy)**. Do not worry! They are still connected to their respective escalation chains and will continue to to
> execute as they always have.
> <br/><br/>
> The **(Legacy)** webhook is no longer editable due to changes to the internal representation. If you need to edit it
> you must use the `Make a copy` action in the menu and make your changes there. This will create the webhook in the
> new format. Be sure to change your escalation chains to point to the new copy otherwise it will not be active. The
> **(Legacy)** webhook can then be deleted.

Outgoing webhooks are used by Grafana OnCall to send data to a URL in a flexible way. These webhooks can be
triggered from a variety of event types and make use of Jinja2 to transform data into the format required at
the destination URL. Each outgoing webhook receives contextual data when executed which can be processed by
Jinja2 templates to customize the request being sent.

## Creating an outgoing webhook

To create an outgoing webhook navigate to **Outgoing Webhooks** and click **+ Create**. On this screen outgoing
webhooks can be viewed, edited and deleted. To create the outgoing webhook click **New Outgoing Webhook** and then
select a preset based on what you want to do. A simple webhook will POST alert group data as a selectable escalation
step to the specified url. If you require more customization use the advanced webhook which provides all of the
fields described below.

### Outgoing webhook fields

The outgoing webhook is defined by the following fields. For more information about template usage
see [Outgoing webhook templates](#outgoing-webhook-templates) section.

#### ID

This field is generated after an outgoing webhook has been created. It is used to reference the responses of
other webhooks, see [Advanced Usage - Using response data](#using-response-data) for more details.

#### Name

Display name of the outgoing webhook.

| Required | [Template Accepted](#outgoing-webhook-templates) | Default Value |
| :------: | :----------------------------------------------: | :-----------: |
|    ✔️    |                        ❌                        |    _Empty_    |

#### Enabled

Controls whether the outgoing webhook will trigger or is ignored.

| Required | [Template Accepted](#outgoing-webhook-templates) | Default Value |
| :------: | :----------------------------------------------: | :-----------: |
|    ✔️    |                        ❌                        |    _True_     |

#### Assign to Team

Sets which team owns the outgoing webhook for filtering and visibility.
This setting does not restrict outgoing webhook execution to events from the selected team.

| Required | [Template Accepted](#outgoing-webhook-templates) | Default Value |
| :------: | :----------------------------------------------: | :-----------: |
|    ❌    |                        ❌                        |    _Empty_    |

#### Trigger Type

The type of event that will cause this outgoing webhook to execute. The types of triggers are:

- [Escalation Step](#escalation-step)
- [Alert Group Created](#alert-group-created)
- [Acknowledged](#acknowledged)
- [Resolved](#resolved)
- [Silenced](#silenced)
- [Unsilenced](#unsilenced)
- [Unresolved](#unresolved)
- [Unacknowledged](#acknowledged)

For more details about types of triggers see [Event types](#event-types)

| Required | [Template Accepted](#outgoing-webhook-templates) | Default Value |
| :------: | :----------------------------------------------: | :-----------: |
|    ✔️    |                        ❌                        |    _None_     |

#### HTTP Method

The HTTP method used in the request made by the outgoing webhook. This should match what is required by the URL
you are sending to.

| Required | [Template Accepted](#outgoing-webhook-templates) | Default Value |
| :------: | :----------------------------------------------: | :-----------: |
|    ✔️    |                        ❌                        |    _POST_     |

#### Integrations

Restricts the outgoing webhook to only trigger if the event came from a selected integration.
If no integrations are selected the outgoing webhook will trigger for any integration.

| Required | [Template Accepted](#outgoing-webhook-templates) | Default Value |
| :------: | :----------------------------------------------: | :-----------: |
|    ❌    |                        ❌                        |    _None_     |

#### Webhook URL

The destination URL the outgoing webhook will make a request to. This must be a FQDN.

> ⚠️ **Note** the destination server must respond back within 4 seconds (by default) or it will result in a timeout
> For open source deployments, this timeout is configurable by setting the environment variable OUTGOING_WEBHOOK_TIMEOUT
> (this can be seen in the "Response Body" under the "Last Run" section)

| Required | [Template Accepted](#outgoing-webhook-templates) | Default Value |
| :------: | :----------------------------------------------: | :-----------: |
|    ✔️    |                        ✔️                        |    _Empty_    |

#### Webhook Headers

Headers to add to the outgoing webhook request.

| Required | [Template Accepted](#outgoing-webhook-templates) | Default Value |
| :------: | :----------------------------------------------: | :-----------: |
|    ❌    |                        ✔️                        |    _Empty_    |

#### Username

Username to use when making the outgoing webhook request.

| Required | [Template Accepted](#outgoing-webhook-templates) | Default Value |
| :------: | :----------------------------------------------: | :-----------: |
|    ❌    |                        ❌                        |    _Empty_    |

#### Password

Password to use when making the outgoing webhook request.

| Required | [Template Accepted](#outgoing-webhook-templates) | Default Value |
| :------: | :----------------------------------------------: | :-----------: |
|    ❌    |                        ❌                        |    _Empty_    |

#### Authorization Header

Authorization header to use when making the outgoing webhook request.

| Required | [Template Accepted](#outgoing-webhook-templates) | Default Value |
| :------: | :----------------------------------------------: | :-----------: |
|    ❌    |                        ❌                        |    _None_     |

#### Trigger Template

A template used to dynamically determine whether the webhook should execute based on the content of the payload.
If the template evaluates to Empty, True or 1 the webhook will execute.

| Required | [Template Accepted](#outgoing-webhook-templates) | Default Value |
| :------: | :----------------------------------------------: | :-----------: |
|    ❌    |                        ✔️                        |    _Empty_    |

#### Data

The main body of the request to be sent by the outgoing webhook.

| Required | [Template Accepted](#outgoing-webhook-templates) | Default Value |
| :------: | :----------------------------------------------: | :-----------: |
|    ❌    |                        ✔️                        |    _Empty_    |

#### Forward All

Toggle to send the entire webhook payload instead of using the values in the **Data** field

| Required | [Template Accepted](#outgoing-webhook-templates) | Default Value |
| :------: | :----------------------------------------------: | :-----------: |
|    ❌    |                        ❌                        |    _False_    |

## Labels

> **Note:** Labels are currently available only in cloud.

Webhook labels allow to pass labels data to a 3'rd party.
Label data will be included in the webhook payload, along with alert group and integration labels.
It could be useful such use-cases as delivering Alert Groups with severity to the ServiceNow or
forwarding the cluster name to the GitHub issue.
Check this [template example][labels_webhook_template] to see how you can include labels in the webhook data.

Editing Webhook Labels:
To edit the labels associated with a webhook, follow these steps:

1. Navigate to the Webhooks tab.
2. Select an integration from the list of enabled integrations.
3. Click the three dots next to the webhook name and choose Edit Settings.
4. Define a key and value for the label:
   - Select existing keys and values from the dropdown list, or
   - Type new keys and values into the fields, accepting with the enter/return key.
5. To add more labels, click the Add button. Labels can also be removed using the X button next to the key-value pair.
6. Click Save to apply the changes.

To filter webhooks based on labels, use the following steps:

1. Navigate to the Webhooks tab.
2. Locate the Search or Filter Results… dropdown and select Label.
3. Start typing to find suggestions and select the desired key-value pair for filtering. Currently, it's only possible to filter by key-value pairs.

## Outgoing webhook templates

The fields that accept a Jinja2 template in outgoing webhooks are able to process data to customize the output.
The following is an example of the data available to access from a template. Some data depending on the timing
of the webhook and the triggering event may not always be available,
see [field descriptions](#outgoing-webhook-data-fields) specific details. The format you use to call the variables
must match the structure of how the fields are nested in the data.

```json
{
  "event": {
    "type": "resolve",
    "time": "2023-04-19T21:59:21.714058+00:00"
  },
  "user": {
    "id": "UVMX6YI9VY9PV",
    "username": "admin",
    "email": "admin@localhost"
  },
  "alert_group": {
    "id": "I6HNZGUFG4K11",
    "integration_id": "CZ7URAT4V3QF2",
    "route_id": "RKHXJKVZYYVST",
    "alerts_count": 1,
    "state": "resolved",
    "created_at": "2023-04-19T21:53:48.231148Z",
    "resolved_at": "2023-04-19T21:59:21.714058Z",
    "acknowledged_at": "2023-04-19T21:54:39.029347Z",
    "title": "Incident",
    "permalinks": {
      "slack": null,
      "telegram": null,
      "web": "https://**********.grafana.net/a/grafana-oncall-app/alert-groups/I6HNZGUFG4K11"
    },
    "labels": {
      "region": "eu-1"
    }
  },
  "alert_group_id": "I6HNZGUFG4K11",
  "alert_payload": {
    "endsAt": "0001-01-01T00:00:00Z",
    "labels": {
      "region": "eu-1",
      "alertname": "TestAlert"
    },
    "status": "firing",
    "startsAt": "2018-12-25T15:47:47.377363608Z",
    "annotations": {
      "description": "This alert was sent by user for the demonstration purposes"
    },
    "generatorURL": ""
  },
  "integration": {
    "id": "CZ7URAT4V3QF2",
    "type": "webhook",
    "name": "Main Integration - Webhook",
    "team": "Webhooks Demo",
    "labels": {
      "component": "demo"
    }
  },
  "notified_users": [],
  "users_to_be_notified": [],
  "responses": {
    "WHP936BM1GPVHQ": {
      "id": "7Qw7TbPmzppRnhLvK3AdkQ",
      "created_at": "15:53:50",
      "status": "new",
      "content": {
        "message": "Ticket created!",
        "region": "eu"
      }
    }
  },
  "webhook": {
    "name": "demo_hook",
    "labels": {}
  }
}
```

### Outgoing webhook data fields

#### `event`

Context information about the event that triggered the outgoing webhook.

- `{{ event.type }}` - Lower case string matching [type of event](#event-types)
- `{{ event.time }}` - Time event was triggered

#### `user`

Information about the user if the source of the event was a user. If a user acknowledges an alert group after
receiving a notification this field will have that user's information. If an alert group was auto-resolved based
on criteria in the integration this field will be empty.

- `{{ user.id }}` - [UID](#uid) of the user within Grafana OnCall
- `{{ user.username }}` - Username in Grafana
- `{{ user.email }}` - Email associated with user's Grafana account

#### `alert_group`

Details about the alert group associated with this event.

- `{{ alert_group.id }}` - [UID](#uid) of alert group
- `{{ alert_group.integration_id }}` - [UID](#uid) of integration that alert came through
- `{{ alert_group.route_id }}` - [UID](#uid) of route of integration that alert came through
- `{{ alert_group.alerts_count }}` - Count of alerts in alert group
- `{{ alert_group.state }}` - Current state of alert group
- `{{ alert_group.created_at }}` - Timestamp alert group was created
- `{{ alert_group.resolved_at }}` - Timestamp alert group was resolved (None if not resolved yet)
- `{{ alert_group.acknowledged_at }}` - Timestamp alert group was acknowledged (None if not acknowledged yet)
- `{{ alert_group.title }}` - Title of alert group
- `{{ alert_group.permalinks }}` - Links to alert group in web and chat ops if available
- `{{ alert_group.labels }}` - Labels parsed by OnCall from the first alert in the alert group

#### `{{ alert_group_id }}`

UID of alert group, same as `{{ alert_group.id }}` (For convenience and compatibility with earler versions of Grafana OnCall)

#### `alert_payload`

Content of the first alert in the alert group. Content will depend on what the alert source has sent.
Some commonly used fields are:

- `{{ alert_payload.labels.alertname }}`
- `{{ alert_payload.annotations.description }}`

#### `integration`

Details about the integration that received this alert

- `{{ integration.id }}` - [UID](#uid) of integration
- `{{ integration.type }}` - Type of integration (grafana, alertmanager, webhook, etc.)
- `{{ integration.name }}` - Name of integration
- `{{ integration.team }}` - Team integration belongs to if integration is assigned to a team
- `{{ integration.labels }}` - Labels assigned to integration

#### `notified_users`

Array of users that have received notifications about the associated alert group. Each user element in the array
consists of `id`,`username`,`email`. Depending on timing of events and notifications this might not be populated yet
if notifications are still in progress. Access as `{{ notified_users[0].username }}` for example.

#### `users_to_notify`

Array of users that could potentially be notified based on the configured escalation chain. Each user element in the array
consists of `id`,`username`,`email`. Array elements are ordered based on the order users will be notified with the
first element being the user that will be notified next. Like `notified_users` depending on timing of notifications
a user in this array may have already been notified by the time this data is being processed. Access as
`{{ users_to_notify[0].username }}` for example.

#### `responses`

The responses field is used to access the response data of other webhooks that are associated with this alert group.
The keys inside responses are the [UID](#uid) of other outgoing webhooks. The values inside each response is the latest
response of the referenced webhook when it was executed on behalf of the current alert group.
See [Advanced Usage - Using response data](#using-response-data) for more details. Access as
`{{ responses["WHP936BM1GPVHQ"].content.message }}` for example

#### `webhook`

Details about the triggered webhook

- `{{ webhook.id }}` - [UID](#uid) of webhook
- `{{ webhook.name }}` - Name of webhook
- `{{ webhook.labels }}` - Labels assigned to webhook

### UID

Templates often use UIDs to make decisions about what actions to take if you need to find the UID of an object
in the user interface to reference they can be found in the following places:

- Outgoing Webhook - In the table there is an info icon, UID displayed on hover, click to copy to clipboard
- Integration - In integrations beside the name is an info icon, UID displayed on hover, click to copy to clipboard
- Routes - With an integration selected beside Send Demo Alert is an infor icon, UID displayed on hover,
  click to copy to clipboard
- Alert group - When viewing an alert group UID is visible in the browser URL
- User - When viewing a user's profile UID is visible in the browser URL

UIDs are also visible in the browser URL when a specific object is selected for view or edit.

- Outgoing Webhook - In the table there is an info icon, UID displayed on hover, click to copy to clipboard
- Integration - In integrations beside the name is an info icon, UID displayed on hover, click to copy to clipboard
- Routes - With an integration selected beside Send Demo Alert is an infor icon, UID displayed on hover,
  click to copy to clipboard
- Alert group - When viewing an alert group UID is visible in the browser URL
- User - When viewing a user's profile UID is visible in the browser URL

UIDs are also visible in the browser URL when a specific object is selected for view or edit.

### Template examples

#### Data in a json body

The following is an example of an entry in the Data field that would return an alert name and description.

```json
{
  "name": "{{ alert_payload.labels.alertname }}",
  "message": "{{ alert_payload.annotations.description }}"
}
```

#### Data in a query parameter

Here is an example using the user's email address as part of a URL:

```jinja2
https://someticketsystem.com/new-ticket?assign-user={{ user.email }}
```

#### JSON webhook payload with the alert-group labels

This example shows how to construct a custom webhook payload from various webhook data fields and output it as a JSON object

```jinja2
{%- set payload = {} -%}
{# add alert group labels #}
{%- set payload = dict(payload, **{"labels": alert_group.labels}) -%}
{# add some other fields from webhook data just for example #}
{%- set payload = dict(payload, **{"event": event.type, "integration": integration.name}) -%}
{# encode payload dict to json #}
{{ payload | tojson }}
```

#### Note about JSON

Take this template for example:

```jinja2
{
  "labels": "{{ alert_payload.labels }}"
}
```

It will result in the following (Invalid JSON due to single quotes):

```json
{
  "labels": {'region': 'eu-1', 'alertname': 'TestAlert'}
}
```

To fix change the template to:

```tempate
{
  "labels": {{ alert_payload.labels | tojson }}
}
```

Now the result is correct:

```json
{
  "labels": {
    "alertname": "TestAlert",
    "region": "eu-1"
  }
}
```

## Event types

### Escalation Step

`event.type` `escalation`

This event will trigger when the outgoing webhook is included as a step in an escalation chain.

### Alert Group Created

`event.type` `alert group created`

This event will trigger when a new alert group is created.

### Acknowledged

`event.type` `acknowledge`

This event will trigger when a user acknowledges an alert group or an alert group is auto-acknowledged
by the integration.

### Resolved

`event.type` `resolve`

This event will trigger when a user resolves an alert group or an alert group is auto-resolved
by the integration.

### Silenced

`event.type` `silence`

This event will trigger when a user silences an alert group.

### Unsilenced

`event.type` `unsilence`

This event will trigger when a user unsilences an alert group or a silence expires.

### Unresolved

`event.type` `unresolve`

This event will trigger when a user unresolves an alert group.

### Unacknowledged

`event.type` `unacknowledge`

This event will trigger when a user unacknowledges an alert group.

## Viewing status of outgoing webhooks

In the outgoing webhooks table if a webhook is enabled **Last Run** will have the following information:

- Timestamp outgoing webhook was triggered
- HTTP response code

If more information is required you can click **Status** in the table. The status drawer shows the following:

- Webhook Name
- Webhook UID
- Trigger Type
- Last Run Time
- URL
- Response Code
- Response Body
- Trigger Template
- Request Headers
- Request Data

In the status drawer if a field makes use of a template it will display both the template and the result
otherwise it will only display the value. Fields which are not used are not shown.

## Advanced usage

### Using trigger template field

The [trigger template field](#trigger-type) can be used to provide control over whether a webhook will execute.
This is useful in situations where many different kinds of alerts are going to the same integration but only some of
them should call the webhook. To accomplish this the trigger template field can contain a template that will process
data from the alert group and evaluate to empty, True or 1 if the webhook should execute, any other values will result
in the webhook not executing.

### Using response data

The `responses` section of the payload makes available the responses of other webhooks that have acted on the same
alert group. To access them `responses` uses the `id` of the webhook as a key. The `id` can be found by hovering
over the info icon, clicking will copy the `id` to the clipboard. The response data of the most recent
execution of the webhook for this same alert group can be accessed this way.

The typical application of this is where a webhook will create a ticket in another system and OnCall needs to use
the `id` of that ticket to keep its status synchronized with the state changes being made in OnCall.

### Advanced examples

Integrate with third-party services:

- [JIRA]({{< relref "../integrations/jira" >}})
- [ServiceNow]({{< relref "../integrations/servicenow" >}})
- [Zendesk]({{< relref "../integrations/zendesk" >}})

{{< section >}}

{{% docs/reference %}}
[labels_webhook_template]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/outgoing-webhooks/#json-webhook-payload-with-the-alert-group-labels
[labels_webhook_template]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/outgoing-webhooks/#json-webhook-payload-with-the-alert-group-labels
{{% /docs/reference %}}
