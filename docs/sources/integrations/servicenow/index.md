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

   After creating the user, generate a password for the user (use the **Set Password** button) and save it for later use.
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
     * `New -> Triggered`
     * `In Progress -> Acknowledged`
     * `Resolved -> Resolved`
     * `Silenced -> Not Selected`
8. Generate a ServiceNow Business Rule script. This script will allow your ServiceNow instance to send updates to
Grafana OnCall. See the next step for more details on how to create the Business Rule in ServiceNow.
9. On your ServiceNow instance, navigate to **System Definition** > **Business Rules** and click **New**.
Fill in the following details:
   * Name: `grafana-oncall`
   * Table: `incident`
   * Active: ✔
   * Advanced: ✔
   * When to run > When: `after`
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
integration. To do this:

1. Navigate to the **Outgoing** tab of an existing ServiceNow integration.
2. Click **Connect** and select the integrations you want to connect, then click **Connect**.
3. Enable the **backsync** option if you want alert groups from connected integrations to be updated from ServiceNow.
   If disabled, Grafana OnCall will only send alerts to ServiceNow, but not receive updates back.
4. Test the connection by creating a demo alert for the connected integration.
   * Verify that an incident is created in ServiceNow.
   * Verify that incident state changes in ServiceNow are reflected in Grafana OnCall, and vice-versa.

## Advanced usage

TBD
