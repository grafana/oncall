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

"Integration" is a main entry point for alerts being consumed by OnCall. Rendering, grouping and routing are configured
within integrations.

"Integration" is a set of Jinja2 templates which is transforming alert payload to the format suitable to OnCall.
You could check pre-configured templates in the list of avaliable integrations (Integrations ->
"New integration to receive alerts"), create your own or adjust existing.

Read more about Jinja2 templating used in OnCall [here]({{< relref "../jinja2-templating" >}}).

Alert flow within integration:

1. Alert is registered by unique integration url (or [e-mail]({{< relref "inbound-email" >}}) in case of inbound e-mail
integration)
2. If there is a non-resolved "alert group" with the same "grouping id", alert will be added to this "alert group".
3. If there is no non-resolved "alert group" with the same "grouping id", new "alert group" will be issued.
4. New "alert group" will be routed using routing engine and escalation chain will be started (TODO: link).

## Configure and manage integrations

You can configure and manage your integrations from the **Integrations** tab in Grafana OnCall. The following sections
describe how to configure and customize your integrations to ensure alerts are treated appropriately.

### Connect an integration

To configure an integration for Grafana OnCall:

1. In Grafana OnCall, navigate to the **Integrations** tab and click **+ New integration to receive alerts**.
2. Select an integration from the provided options, if the integration you want isn’t listed, then select **Webhook**.
3. Follow the configuration steps on the integration settings page.
4. Complete any necessary configurations in your tool to send alerts to Grafana OnCall.

### Manage integrations

To manage existing integrations, navigate to the **Integrations** tab in Grafana OnCall and select the integration
you want to manage.

#### Manage integration behaviour and rendering

"Integration templates" are Jinja2 templates which are applied to each alert to define it's rendering and behaviour.
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

Read more about Jinja2 (TODO: link) in a specific section.

#### Edit integration name

To edit the name of an integration:

1. Navigate to the **Integrations** tab, select an integration from the list of enabled integrations.
2. Click the **pencil icon** next to the integration name.
3. Provide a new name and click **Update**.

{{< section >}}
