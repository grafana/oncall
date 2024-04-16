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
labels:
  products:
    - cloud
title: ServiceNow
weight: 500
---

# Integrate Grafana OnCall with ServiceNow

> This integration is not available in OSS version

The bi-directional ServiceNow integration can create and update incidents in ServiceNow based on Grafana OnCall alert
groups, and vice-versa. This integration supports alerts originating from ServiceNow or other integrations such as
Alertmanager, Grafana Alerting, and others.

The integration can automatically:

* Create an incident in ServiceNow when an alert group is created in OnCall.
* Update the incident state in ServiceNow when the alert group status changes in OnCall.
* Create an alert group in OnCall when an incident is created in ServiceNow.
* Update the alert group status in OnCall when the incident state changes in ServiceNow.

## Prerequisites

1. Create a new ServiceNow user to be used by Grafana OnCall. On your ServiceNow instance,
navigate to **User Administration** > **Users** and click **New**. Fill in the following details:
   * Username: `grafana-oncall`
   * First name: `Grafana OnCall`
   * Active: ✔
   * Web service access only: ✔

   After creating the user, generate and save a password using the Set Password button for later use.
2. Grant the following roles to the user (use the **Roles** tab):
   * `itil` (allows creating and updating incidents)
   * `personalize_choices` (allows fetching the list of available incident states)

## Create integration

1. On the **Integrations** tab, click **+ New integration**.
2. Select **ServiceNow** from the list of available integrations.
3. Enter a name and description for the integration.
4. Enter ServiceNow credentials (instance URL, username, and password) and verify the connection.
5. Make sure **Create default outgoing webhooks** is enabled. This will create the necessary webhooks in Grafana OnCall
to send alerts to ServiceNow.
6. Click **Create integration**.
7. Map ServiceNow incident states to OnCall alert group statuses. Example:
     * `Firing -> New`
     * `Acknowledged -> In Progress`
     * `Resolved -> Resolved`
     * `Silenced -> Not Selected`
8. Generate a ServiceNow Business Rule script and copy it to your clipboard. This script will allow your ServiceNow
instance to send updates to Grafana OnCall. You won't be able to see the script again after closing the
dialog, but you can regenerate it at any time in integration settings. See the next step for more details on how to
create a Business Rule in ServiceNow using the generated script.
9. On your ServiceNow instance, navigate to **System Definition** > **Business Rules** and click **New**.
Fill in the following details:
   * Name: `grafana-oncall`
   * Table: `incident`
   * Active: ✔
   * Advanced: ✔
   * When to run > When: `before`
   * When to run > Insert: ✔
   * When to run > Update: ✔
   * Advanced > Script: Paste the generated script

    Click **Submit** to save the Business Rule.
10. In Grafana OnCall, click **Proceed** to complete the integration setup.

## Test the integration

1. Create a new incident in ServiceNow.
2. Verify that a new alert group is created in Grafana OnCall.
3. Acknowledge the alert group in Grafana OnCall, and verify that the incident state is updated in ServiceNow.
4. Resolve the incident in ServiceNow, and verify that the alert group status is updated in Grafana OnCall.

## Connect other integrations

You can connect other integrations such as Alertmanager, Grafana Alerting, and others to an existing ServiceNow
integration. When connected, Grafana OnCall will send alerts from the connected integrations to ServiceNow, and update
alert groups on the connected integrations based on incident state changes in ServiceNow. Connected integrations will
use the same ServiceNow credentials and outgoing webhooks as the ServiceNow integration they are connected to.

To connect other integrations:

1. Navigate to the **Outgoing** tab of an existing ServiceNow integration.
2. Use the **Send data from other integrations** section to connect other integrations.
3. Enable the **backsync** option if you want alert groups from connected integrations to be updated from ServiceNow.
   If disabled, Grafana OnCall will only send alerts to ServiceNow, but not receive updates back.
4. Test the connection by creating a demo alert for the connected integration.
   * Verify that an incident is created in ServiceNow.
   * Verify that incident state changes in ServiceNow are reflected in Grafana OnCall, and vice-versa.

## Advanced usage

You can customize the integration behaviour by editing the outgoing webhooks on the **Outgoing** tab of the integration.

### Custom incident fields

You can set custom fields on ServiceNow incidents. To do so, edit the **Alert group created** webhook on
the **Outgoing** tab of the integration.

Example: to set the "urgency" field based on alert group labels, add the following to **Data template**:

 ```json
 {
   ...,
   "urgency": "{{ alert_group.labels.urgency }}"
 }
 ```

   Refer to [Outgoing webhook templates] and [Alert group labels] for more info.

{{% docs/reference %}}
[Alert group labels]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/integrations#alert-group-labels"
[Alert group labels]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/integrations#alert-group-labels"

[Outgoing webhook templates]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/outgoing-webhooks#outgoing-webhook-templates"
[Outgoing webhook templates]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/outgoing-webhooks#outgoing-webhook-templates"
{{% /docs/reference %}}
