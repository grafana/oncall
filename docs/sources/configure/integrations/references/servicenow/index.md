---
title: ServiceNow integration for Grafana OnCall
menuTitle: ServiceNow
description: Learn how to configure the ServiceNow integration for Grafana OnCall.
weight: 0
keywords:
  - OnCall
  - Integrations
  - Alerts
  - ServiceNow
  - Notifications
labels:
  products:
    - cloud
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/references/servicenow
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/servicenow
  - /docs/grafana-cloud/alerting-and-irm/oncall/integrations/servicenow
  - /docs/oncall/latest/integrations/servicenow/
  - ../integrations/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/servicenow
refs:
  alert-group-labels:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/integrations/labels/#alert-group-labels
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/labels/#alert-group-labels
  outgoing-webhook-templates:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/integrations/outgoing-webhooks/#outgoing-webhook-templates
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/outgoing-webhooks/#outgoing-webhook-templates
---

# ServiceNow integration for Grafana OnCall

{{< admonition type="note" >}}
This integration is available exclusively on Grafana Cloud.
{{< /admonition >}}

Integrate ServiceNow with Grafana OnCall for bidirectional functionality that automatically creates and updates incidents in ServiceNow based on Grafana OnCall alert
groups, and vice versa. Whether your alerts originate from ServiceNow or another integration like
Alertmanager or Grafana Alerting, you can manage updates and status changes directly from ServiceNow.

Use this integration to automate the following processes:

* Create an incident in ServiceNow when an alert group is created in OnCall.
* Update the incident state in ServiceNow when the alert group status changes in OnCall.
* Create an alert group in OnCall when an incident is created in ServiceNow.
* Update the alert group status in OnCall when the incident state changes in ServiceNow.

## Before you begin

Before configuring the integration, ensure you or your ServiceNow Admin have created a Service account specifically for Grafana OnCall integration.

Follow these steps to create a ServiceNow user for Grafana OnCall:

1. In ServiceNow,navigate to **User Administration** > **Users** and click **New**.
1. Fill in the following details:
   * Username: `grafana-oncall`
   * First name: `Grafana OnCall`
   * Active: ✔
   * Web service access only: ✔
1. After creating the user, generate a password using the **Set Password** button. Securely store the password for later use.
1. Navigate to the **Roles** tab and grant the following roles to the user:
   * `itil` (for incident creation and updates)
   * `personalize_choices` (to fetch the list of available incident states)

## Configure ServiceNow integration

### Create integration

1. On the **Integrations** tab in Grafana OnCall, click **+ New integration**.
1. Select **ServiceNow** from the list of available integrations.
1. Enter a name and description for the integration.
1. Enter ServiceNow credentials (instance URL, username, and password of the [Grafana OnCall user](#before-you-begin)) and verify the connection.
1. Ensure **Create default outgoing webhooks** is enabled to create necessary webhooks in Grafana OnCall for sending alerts to ServiceNow.
1. Click **Create integration**.

### Map incident states

Map ServiceNow incident states to OnCall alert group statuses.

Example:

* `Firing -> New`
* `Acknowledged -> In Progress`
* `Resolved -> Resolved`
* `Silenced -> Not Selected`

### Generate Business Rule script

Generate a ServiceNow Business Rule script to enable your ServiceNow instance to send updates to Grafana OnCall.

{{< admonition type="note" >}}
You can't view the script again after closing the dialog, but you can regenerate it at any time in integration settings.
{{< /admonition >}}

1. Generate a new ServiceNow Business Rule script and copy it to your clipboard.
1. In ServiceNow, navigate to **System Definition** > **Business Rules** and click **New**.
1. Fill in the following details:
   * Name: `grafana-oncall`
   * Table: `incident`
   * Active: ✔
   * Advanced: ✔
   * When to run > When: `before`
   * When to run > Insert: ✔
   * When to run > Update: ✔
   * Advanced > Script: Paste the generated script
1. Click **Submit** to save the Business Rule.

In Grafana OnCall, click **Proceed** to complete the integration setup.

## Test the integration

1. Create a new incident in ServiceNow.
2. Verify that a new alert group is created in Grafana OnCall.
3. Acknowledge the alert group in Grafana OnCall, and verify that the incident state is updated in ServiceNow.
4. Resolve the incident in ServiceNow, and verify that the alert group status is updated in Grafana OnCall.

## Connect other integrations

You can connect other integrations such as Alertmanager, Grafana Alerting, and others to your ServiceNow integration for a consolidated workflow.
When connected, Grafana OnCall sends alerts from the connected integrations to ServiceNow and update alert groups on the connected integrations based on incident
state changes in ServiceNow.
Connected integrations utilize the same ServiceNow credentials and outgoing webhooks as the ServiceNow integration they are connected to.

To connect other integrations:

1. Navigate to the **Outgoing** tab of an existing ServiceNow integration.
2. Use the **Send data from other integrations** section to connect other integrations.
3. Enable the **backsync** option if you want alert groups from connected integrations to be updated from ServiceNow.
If disabled, Grafana OnCall will only send alerts to ServiceNow, but not receive updates back.
4. Test the connection by creating a demo alert for the connected integration.
   * Verify that an incident is created in ServiceNow.
   * Verify that incident state changes in ServiceNow are reflected in Grafana OnCall, and vice-versa.

## Advanced usage

Customize the integration behavior according to your needs by editing the outgoing webhooks on the **Outgoing** tab of the integration.

### Custom incident fields

You can set custom fields on ServiceNow incidents. To do so, edit the **Alert group created** webhook on
the **Outgoing** tab of the integration.

Example: Set the "urgency" field based on alert group labels, add the provided JSON to **Data template**:

 ```json
 {
   ...,
   "urgency": "{{ alert_group.labels.urgency }}"
 }
 ```

For more information, refer to [Outgoing webhook templates](ref:outgoing-webhook-templates) and [Alert group labels](ref:alert-group-labels).
