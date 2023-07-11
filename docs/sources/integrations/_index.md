---
canonical: https://grafana.com/docs/oncall/latest/integration-with-alert-sources/
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

Read more about Jinja2 templating used in OnCall [here][jinja2-templating].

## Learn Alert Flow Within Integration

1. An Alert is received on an integration's **Unique URL** as an HTTP POST request with a JSON payload (or via
[e-mail]({{< relref "inbound-email" >}}), for inbound e-mail integrations)
1. Routing is determined for the incoming alert, by applying the [Routing Template][routing-template]
1. Alert Grouping is determined based on [Grouping Id Template][behavioral-template]
1. An Alert Group may be acknowledged or resolved with status `_ by source` based on
[Behaviour Templates][behavioral-template]
1. The Alert Group is available in Web, and can be published to messengers, based on the Route's **Publish to Chatops** configuration.
It is rendered using [Appearance Templates][appearance-template]
1. The Alert Group is escalated to uers based on the Escalation Chains selected for the Route
1. Users can perform actions listed in [Learn Alert Workflow][learn-alert-workflow] section

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

- Review and customise grouping, autoresolution, autoacknowledge, etc [templates][jinja2-templating]
if you want to customise alert behaviour for your team
- Review and customise [other templates][jinja2-templating] to change how alert groups are displayed
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
to the heartbeat endpoint. If OnCall doen't receive one of these alerts, it will create an new alert group and escalate it

1. Go to Integration page and click **Three dots**
1. Select **Heartbeat Settings**
1. Set **Heartbeat interval**
1. Copy **Endpoint** into you monitoring system.

More specific instructions can be found in a specific integration's documentation.

#### Behaviour and rendering templates example

"Integration templates" are Jinja2 templates which are applied to each alert to define it's rendering and behaviour.

Read more in [Templates guide][jinja2-templating]

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
1. Click the **three dots** next to the integration name and select **Integration settings**.
1. Provide a new name, description, and team, and click **Save**.

## List of available integrations

{{< section >}}

{{% docs/reference %}}
[appearance-template]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/jinja2-templating#appearance-template"
[appearance-template]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/jinja2-templating#appearance-template"

[behavioral-template]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/jinja2-templating#behavioral-template"
[behavioral-template]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/jinja2-templating#behavioral-template"

[jinja2-templating]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/jinja2-templating"
[jinja2-templating]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/jinja2-templating"

[learn-alert-workflow]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/get-started#learn-alert-workflow"
[learn-alert-workflow]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/get-started#learn-alert-workflow"

[routing-template]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/jinja2-templating#routing-template"
[routing-template]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/jinja2-templating#routing-template"
{{% /docs/reference %}}
