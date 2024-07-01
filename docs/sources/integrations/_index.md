---
canonical: https://grafana.com/docs/oncall/latest/integrations/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - amixr
  - oncall
  - integrations
title: Integrations
weight: 500
---

# Integrations

An "Integration" is a main entry point for alerts being consumed by Grafana OnCall.
Integrations receive alerts on a unique API URL, interprets them using a set of templates tailored for the monitoring system, and starts
escalations.

For more information about the templating used in OnCall, refer to [Jinja2 templating][].

## Learn Alert Flow Within Integration

1. An Alert is received on an integration's **Unique URL** as an HTTP POST request with a JSON payload (or via
[Inbound email][], for inbound email integrations)
1. Routing is determined for the incoming alert, by applying the [Routing Template][]
1. Alert Grouping is determined based on [Grouping Id Template][]
1. An Alert Group may be acknowledged or resolved with status `_ by source` based on its [Behavioral templates][]
1. The Alert Group is available in Web, and can be published to messengers, based on the Route's **Publish to Chatops** configuration.
It is rendered using [Appearance templates][]
1. The Alert Group is escalated to users based on the Escalation Chains selected for the Route
1. Users can perform actions listed in [Learn about the Alert Workflow][] section

## Configure and manage integrations

You can configure and manage your integrations from the **Integrations** tab in Grafana OnCall. The following sections
describe how to configure and customize your integrations to ensure alerts are treated appropriately.

### Connect an integration

To configure an integration for Grafana OnCall:

1. In Grafana OnCall, navigate to the **Integrations** tab and click **+ New integration**.
1. Select an integration type from the [list of available integrations](#list-of-available-integrations).
If the integration you want isn’t listed, then select **Webhook**.
1. Fill in a title and a description for your integration, assign it to a team, and click **Create Integration**.
1. The Integration page will open. Here you will see details about the Integration.
You can use the HTTP Endpoint url to send events from an external monitoring system.
Click the **How to connect** link for more information.
1. Complete any necessary configurations in your tool to send alerts to Grafana OnCall.
1. Click **Send demo alert** to send a test alert to Grafana OnCall.

### Complete the integration configuration

- Review and customise grouping, autoresolution, autoacknowledge templates
if you want to customise alert behaviour for your team
- Review and customise other templates to change how alert groups are displayed
in different parts of Grafana OnCall: UI, messengers, emails, notifications, etc.
- Add routes to your integration to route alerts to different users and teams based on labels or other data
- Connect your escalation chains to routes to notify the right people, at the right time
- Learn [how to start Maintenance Mode](#maintenance-mode) for an integration
- Send demo alerts to an integration to make sure routes, templates, and escalations, are working as expected. Consider using
`Debug Maintenance mode` to avoid sending real notifications to your team

### Manage integrations

To manage existing integrations, navigate to the **Integrations** tab in Grafana OnCall and select the integration
you want to manage.

#### Maintenance Mode

Start maintenance mode when performing scheduled maintenance or updates on your infrastructure, which may trigger false alarms.
There are two possible maintenance modes:

- **Debug** - test routing and escalations without real notifications. Alerts will be processed as usual, but no notifications
will be sent to users.
- **Maintenance** - group alerts into one during infrastructure work.

##### Manage maintenance Mode

1. Go to the Integration page and click **Three dots**
1. Select **Start Maintenance Mode**
1. Select **Debug** or **Maintenance** mode
1. Set the **Duration** of Maintenance Mode
1. Click **Start**
1. If you want to stop maintenance mode before it ends, click **Three dots** and select **Stop Maintenance Mode**

#### Heartbeat monitoring

An OnCall heartbeat acts as a healthcheck for alert group monitoring. You can configure you monitoring to regularly send alerts
to the heartbeat endpoint. If OnCall doesn't receive one of these alerts, it will create an new alert group and escalate it

1. Go to Integration page and click **Three dots**
1. Select **Heartbeat Settings**
1. Set **Heartbeat interval**
1. Copy **Endpoint** into you monitoring system.

If you need to disable heartbeat monitoring on an integration use the **Reset** button to return it to the state of being
inactive. To start the heartbeat monitoring again send a request to the **Endpoint**.

More specific instructions can be found in a specific integration's documentation.

#### Behaviour and rendering templates example

_Integration templates_ are Jinja2 templates which are applied to each alert to define it's rendering and behaviour.
For more information refer to [Jinja2 templating][].

For templates editor:

1. Navigate to the **Integrations** tab, select an integration from the list.
2. Click the **gear icon** next to the integration name.

Here are a few templates responsible for alert group formation:

- **Alert Behaviour, Grouping id** - defining how alerts will be grouped into alert groups. Alerts with the same result
- of executing of this template will be grouped together. For example:

Alert 1 payload:`{"name": "CPU 90%", "cluster": "EU"}`

Alert 2 payload:`{"name": "CPU 90%", "cluster": "US"}`

If we want to group them together by name, we could use template `{{ payload.name }}` which will result to the equal
grouping id "CPU 90%". If we want to group them by region and end up with 2 separate alert groups, we could use such a
template: `{{ payload.region }}}`

- **Alert Behaviour, Acknowledge Condition** - If this template will be rendered as "True" or "1", containing alert
- group will change it's state to "acknowledged".

- **Alert Behaviour, Resolve Condition** - Similar to Acknowledge Condition, will make alert group "resolved".

- **Alert Behaviour, Source Link** - result of rendering of this template will be used in various places of the UI.
Should point to the most specific place in the alert source related to the alert group. Also rendering result will be
available in other templates as a variable `{{ source_link }}`.

#### Edit integration name, description and assigned team

To edit the name of an integration:

1. Navigate to the **Integrations** tab, select an integration from the list of enabled integrations.
2. Click the **three dots** next to the integration name and select **Integration settings**.
3. Provide a new name, description, and team, and click **Save**.

#### Labels

> **Note:** Labels are currently available only in cloud.

Integration labels allows to manage and filter integrations based on specific criteria
and pass these labels down to Alert Groups.
It could be useful to organize integrations by service, region or other custom attribute.  

To assign labels to the integration:

1. Navigate to the **Integrations** tab, select an integration from the list of enabled integrations.
2. Click the **three dots** next to the integration name and select **Integration settings**.
3. Define a Key and Value of the label, either by:
   - Selecting existing key and values from the dropdown list
   - Typing new keys and values into the fields and accepting with enter/return key
4. If you want to add more labels click on **Add** button. You can also remove the label using X button next to the key-value pair.
5. Click **Save**.

To filter integrations by labels:

1. Navigate to the **Integrations** tab
2. Find the **Search or filter results…** dropdown and select **Label**
3. Start typing to find suggestions and select the key-value pair you'd like to filter by.

#### Alert Group Labels

The Alert Group Labeling feature allows users to:

- Assign labels to alert groups
- Filter alert groups by labels
- Customize the Alert Group table
- Pass labels in [Webhooks]

##### Label Assignment Limits

Up to 15 Labels: OnCall allows the assignment of up to 15 labels to an alert group.
If there are more than 15 labels to be assigned, only the first 15 labels (sorted alphabetically)
from the first alert in the group will be assigned.

##### Label Persistence

Once a label is assigned to an alert group, it remains unchanged, even if the label is edited.
This approach considers the label as historical data.

##### Configuration

Alert Group Labeling is configured per-integration, and the settings are accessible in the Alert Group Labeling tab.

To find Alert Group Labeling Settings:

1. Navigate to the **Integrations** tab.
2. Select an integration from the list of enabled integrations.
3. Click the three dots next to the integration name.
4. Choose **Alert Group Labeling**

##### Assign Labels to Alert Groups

###### Pass Down Integration Labels

These labels are automatically assigned to each alert group coming to the integration,
based on the labels assigned to the [integration][integration-labels].

1. Navigate to the Integration Labels section in the Alert Group Labeling tab.
2. Enable/disable passing down specific labels using the toggler.

###### Dynamic & Static Labels

This feature allows you to assign arbitrary labels to alert groups, either by deriving them from the payload or by specifying static values.
Dynamic: label values are extracted from the alert payload using Jinja. Keys remain static.
Static: these are not derived from the payload; both key and value are static.
These labels will not be attached to the integration.

1. In the Alert Group Labeling tab, navigate to Dynamic & Static Labels.
2. Press the **Add Label** button and choose between dynamic or static labels.

For Static Labels:

1. Choose or create key and value from the dropdown list.
2. These labels will be assigned to all alert groups received by this integration.

For Dynamic Labels:

1. Choose or create a key from the dropdown list.
2. Enter a template to parse the value for the given key from the alert payload.

To illustrate the Dynamic Labeling feature, let's consider an example where a dynamic label is created with a `severity` key
and a template to parse values for that key:

```jinja2
{{ payload.get("severity) }}
```

Created dynamic label:
<img src="/static/img/oncall/dynamic-label-example.png" width="700px">

Two alerts were received and grouped to two different alert groups:

Alert 1:

```json
{
  "title": "critical alert",
  "severity": "critical"
}
```

Alert 2:

```json
{
  "title": "warning alert",
  "severity": "warning"
}
```

As a result:

- The first alert group will have a label: `severity: critical`.
- The second alert group will have a label: `severity: warning`.

###### Multi-label extraction template

The Multi-label Extraction Template enables users to extract and modify multiple labels from the alert payload using a single template.
This functionality not only supports dynamic values but also accommodates dynamic keys, with the Jinja template required to result in a valid JSON object.

Consider the following example demonstrating the extraction of labels from a Grafana Alerting payload:

Incoming Payload (trimmed for readability):

```json
{
  ...
  "commonLabels": {
    "job": "node",
    "severity": "critical",
    "alertname": "InstanceDown"
  },
  ...
}
```

Template to parse it:

```jinja2
{{ payload.commonLabels | tojson }}
```

As a result `job`, `severity` and `alertname` labels will be assigned to the alert group:

<img src="/static/img/oncall/mutli-label-extraction-result.png" width="700px">

An advanced example showcases the extraction of labels from various fields of the alert payload, utilizing the Grafana Alerting payload:

```jinja2
{%- set labels = {} -%}
{# add several labels #}
{%- set labels = dict(labels, **payload.commonLabels) -%}
{# add one label #}
{%- set labels = dict(labels, **{"status": payload.status}) -%}
{# add label not from payload #}
{%- set labels = dict(labels, **{"service": "oncall"}) -%}
{# dump labels dict to json string, so OnCall can parse it #}
{{ labels | tojson }}
```

#### Alert Group table customization

Grafana OnCall provides users with the flexibility to customize their Alert Group table to suit individual preferences.
This feature allows users to select and manage the columns displayed in the table, including the option to add custom columns based on labels.
Customizations made to the Alert Group table are user-specific. Each user can personalize their view according to their preferences.
To access customization Navigate to the **Alert Groups** tab and Locate the **Columns** dropdown.

##### Managing default columns

By default, the Columns dropdown provides a list of predefined columns that users can enable or disable based on their preferences.

To manage default columns use the toggler next to each column name to enable or disable its visibility in the table.

##### Adding Custom Columns

Users with admin permissions have the ability to add custom columns based on labels. Follow these steps to add a custom column:

1. Press the Add button in the Columns dropdown. A modal will appear.
2. In the modal, begin typing the name of the labels key you want to create a column for.
3. Select the desired label from the options presented and press the Add button.
4. The new custom column, titled with the label's key, will now be available as an option in the Column Settings for all users.

## List of available integrations

{{< section >}}

{{% docs/reference %}}
[Appearance templates]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating#appearance-templates"
[Appearance templates]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating#appearance-templates"

[Behavioral templates]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating#behavioral-templates"
[Behavioral templates]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating#behavioral-templates"

[Inbound email]: "/docs/oncall -> /docs/oncall/<ONCALL_VERSION>/integrations/inbound-email"
[Inbound email]: "/docs/grafana-cloud -> /docs/oncall/<ONCALL_VERSION>/integrations/inbound-email"

[Jinja2 templating]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating"
[Jinja2 templating]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating"

[Learn about the Alert Workflow]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/set-up/get-started#learn-about-the-alert-workflow"
[Learn about the Alert Workflow]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/set-up/get-started#learn-about-the-alert-workflow"

[Routing template]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating#routing-template"
[Routing template]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating#routing-template"

[Webhooks]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/outgoing-webhooks"
[Webhooks]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/outgoing-webhooks"

[integration-labels]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/integrations/#labels"
[integration-labels]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/integrations/#labels"
{{% /docs/reference %}}
