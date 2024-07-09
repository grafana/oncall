---
title: Configure and manage integrations
menuTitle: Manage integrations
description: An overview of configuration options for Grafana OnCall integrations.
weight: 100
keywords:
  - OnCall
  - Integrations
  - Alert routing
  - Heartbeat monitoring
  - Maintenance mode
  - HTTP Endpoint
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/integration-management/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/integration-management/
  - ../integrations/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/integration-management/
---

# Configure and manage integrations

Integrations with Grafana OnCall help to ensure effective alert handling and efficiency notification routing.
You can configure and manage each integrations settings to meet the needs of the teams that use it.
This guide provides an overview on how to configure, customize and manage your integrations.

You can manage or view your integrations current configuration at any time in the **Integration**s tab of Grafana OnCall.

## Connect an integration

To integrate Grafana OnCall with your chosen tools, follow these steps:

1. Navigate to the **Integrations** tab in Grafana OnCall, and click **+ New integration**.
2. Select your desired integration type from the [list of available integrations](https://grafana.com/docs/grafana-cloud/alerting-and-irm/oncall/integrations/#list-of-available-integrations).
If your desired integration is not listed, select **Webhook**.
3. Provide a title and a description for your integration, assign it to a team, and click **Create Integration**.
4. The Integration page will open, displaying details about the Integration.
The provided HTTP Endpoint URL can be used to send events from an external monitoring system. Click the **How to connect** link for additional information.
5. Configure your tool to send alerts to Grafana OnCall.
6. Click **Send demo alert** to send a test alert to Grafana OnCall.

## Customize the integration

Explore ways to customize the behavior of your alerts from a specific integration:

- Customize alerting grouping, auto-resolution, and auto-acknowledge templates to tailor the alert behavior for your team.
- Modify Appearance templates to customize how alert groups are displayed in various parts of Grafana OnCall, such as the UI, phone and SMS, email, notifications, etc.
- Add routes to your integration to direct alerts to different users and teams based on labels or other data.
- Connect your escalation chains to routes to ensure the right people are notified at the right time.
- Send demo alerts to an integration to validate that routes, templates, and escalations are functioning as expected. Consider using `Debug Maintenance mode` to avoid sending real notifications to your team.

For detailed instructions, refer to:

- [Integration templates]
- [Configure labels]

## Manage Maintenance Mode

Maintenance Mode is useful when performing scheduled maintenance or updates on your infrastructure, which may trigger false alarms. There are two modes:

- **Debug** - Test routing and escalations without real notifications. Alerts will be processed as usual, but no notifications will be sent to users.
- **Maintenance** - Consolidate alerts into one during infrastructure work.

To manage Maintenance Mode:

1. Go to the Integration page and click **Three dots**.
2. Select **Start Maintenance Mode**.
3. Choose **Debug** or **Maintenance** mode.
4. Set the **Duration** of Maintenance Mode.
5. Click **Start**.
6. To stop maintenance mode before its end, click **Three dots** and select **Stop Maintenance Mode**.

## Heartbeat Monitoring

OnCall heartbeat functions as a health check for alert group monitoring. You can configure your monitoring to regularly send alerts to the heartbeat endpoint.
If OnCall doesn’t receive one of these alerts, it will create a new alert group and escalate it.

To configure Heartbeat Monitoring:

1. Go to the Integration page and click **Three dots**.
2. Select **Heartbeat Settings**.
3. Set **Heartbeat interval**.
4. Copy the **Endpoint** into your monitoring system.

If you need to disable heartbeat monitoring on an integration, use the **Reset** button to revert it to the inactive state.
To restart heartbeat monitoring, send a request to the **Endpoint**.

Refer to a specific integration’s documentation for more detailed instructions.

## Manage and edit an integration

Manage your existing integrations by navigating to the **Integrations** tab in Grafana OnCall and selecting the integration you want to manage.

To edit the name of an integration:

1. Navigate to the **Integrations** tab, select an integration from the list of enabled integrations.
2. Click the **three dots** next to the integration name and select **Integration settings**.
3. Provide a new name, description, and team, and click **Save**.

## Explore available integrations

Specific guidance and configuration options for each integration are available at [Integration references].

{{% docs/reference %}}
[Appearance templates]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating#appearance-templates"
[Appearance templates]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating#appearance-templates"

[Behavioral templates]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating#behavioral-templates"
[Behavioral templates]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating#behavioral-templates"

[Inbound email]: "/docs/oncall -> /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/inbound-email"
[Inbound email]: "/docs/grafana-cloud -> /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/inbound-email"

[Jinja2 templating]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating"
[Jinja2 templating]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating"

[Learn about the Alert Workflow]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/set-up/get-started#learn-about-the-alert-workflow"
[Learn about the Alert Workflow]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/set-up/get-started#learn-about-the-alert-workflow"

[Routing template]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating#routing-template"
[Routing template]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating#routing-template"

[Webhooks]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/integrations/outgoing-webhooks"
[Webhooks]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/outgoing-webhooks"

[integration-labels]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/integrations/labels"
[integration-labels]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/labels"

[Integration templates]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating"
[Integration templates]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating"

[Configure labels]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/integrations/labels"
[Configure labels]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/labels"

[Integration references]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/integrations/references"
[Integration references]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references"
{{% /docs/reference %}}
