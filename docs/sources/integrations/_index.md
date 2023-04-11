---
aliases:
  - /docs/oncall/latest/integrations/
canonical: https://grafana.com/docs/oncall/latest/integrations/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - amixr
  - oncall
  - integrations
title: Grafana OnCall integrations
weight: 500
---

# Grafana OnCall integrations

Integrations allow you to connect monitoring systems of your choice to send alerts to Grafana OnCall. Regardless of where
your alerts originate, you can configure alerts to be sent to Grafana OnCall for alert escalation and notification.
Grafana OnCall receives alerts in JSON format via a POST request, OnCall then parses alert data using preconfigured
alert templates to determine alert grouping, apply routes, and determine correct escalation.

There are many integrations that are directly supported by Grafana OnCall. Those that aren’t currently listed in the
Integrations menu can be connected using the webhook integration and configured alert templates.

## Configure and manage integrations

You can configure and manage your integrations from the **Integrations** tab in Grafana OnCall. The following sections
describe how to configure and customize your integrations to ensure alerts are treated appropriately.

### Connect an integration to Grafana OnCall

To configure an integration for Grafana OnCall:

1. In Grafana OnCall, navigate to the **Integrations** tab and click **+ New integration to receive alerts**.
2. Select an integration from the provided options, if the integration you want isn’t listed, then select **Webhook**.
3. Follow the configuration steps on the integration settings page.
4. Complete any necessary configurations in your tool to send alerts to Grafana OnCall.

### Manage Grafana OnCall integrations

To manage existing integrations, navigate to the **Integrations** tab in Grafana OnCall and select the integration
you want to manage.

#### Customize alert templates and grouping

To customize the alert template for an integration:

1. Select an integration from your list of enabled integrations in the **Integrations** tab.
2. Click **Change alert template and grouping**.
3. Select a template to edit from the **Edit template for** dropdown menu.
4. Edit alert templates as needed to customize the fields and content rendered for an alert.

To customize alert grouping for an integration:

1. Click **Change alert template and grouping**.
2. Select **Alert Behavior** from the dropdown menu next to **Edit template for**.
3. Edit the **grouping id**, **acknowledge condition**, and **resolve condition** templates as needed to customize
   your alert behavior.

For more information on alert templates, see
[Configure alerts templates]({{< relref "../alert-behavior/alert-templates" >}})

#### Add Routes

To add a route to an integration using regular expression:

1. Select an integration from your list of enabled integrations in the **Integrations** tab.
2. Click **+ Add Route**.
3. Use python style regex to match on your alert content.
4. Click **Create Route**.
5. Select an escalation chain for “**IF** alert payload matches regex” and “**ELSE**” to specify where to route each
   type of alert.

#### Edit integration name

To edit the name of an integration:

1. Navigate to the **Integrations** tab, select an integration from the list of enabled integrations.
2. Click the **pencil icon** next to the integration name.
3. Provide a new name and click **Update**.

#### Delete integration

To delete an integration:

1. Select an integration from your list of enabled integrations in the **Integrations** tab.
2. Click the **trash can** icon next to the selected integration.
3. Confirm by clicking **Delete**.

{{< section >}}
