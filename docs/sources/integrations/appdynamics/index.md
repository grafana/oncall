---
aliases:
  - add-appdynamics/
  - /docs/oncall/latest/integrations/available-integrations/configure-appdynamics/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-appdynamics/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - AppDynamics
title: AppDynamics
weight: 500
---

# AppDynamics integration for Grafana OnCall

The AppDynamics integration for Grafana OnCall handles health rule violation events sent from AppDynamics actions.
The integration provides grouping and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin][user-and-team-management] to be able to create integrations in Grafana OnCall.

## Configuring Grafana OnCall to Receive Alerts from AppDynamics

1. In the **Integrations** tab, click **+ New integration**.
2. Select **AppDynamics** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.
You will need it when configuring AppDynamics.

## Configuring AppDynamics to Send Alerts to Grafana OnCall

Create a new HTTP Request Template in AppDynamics to send events to Grafana OnCall using the integration URL above.

Refer to
[AppDynamics documentation]
(<https://docs.appdynamics.com/appd/23.x/latest/en/appdynamics-essentials/alert-and-respond/actions/http-request-actions-and-templates>)
for more information on **how to create HTTP Request Templates**:

Use the following values when configuring a new HTTP Request Template:

* Request URL:
  * Method: POST
  * Raw URL: **OnCall Integration URL** from previous section
* Authentication:
  * Type: None
* Payload:
  * MIME Type: application/json
  * Template:

  ```json
  {
    "event": {
      "eventType": "${latestEvent.eventType}",
      "id": "${latestEvent.id}",
      "guid": "${latestEvent.guid}",
      "eventTypeKey": "${latestEvent.eventTypeKey}",
      "eventTime": "${latestEvent.eventTime}",
      "displayName": "${latestEvent.displayName}",
      "summaryMessage": "${latestEvent.summaryMessage}",
      "eventMessage": "${latestEvent.eventMessage}",
      "application": {
        "name": "${latestEvent.application.name}"
      },
      "node": {
        "name": "${latestEvent.node.name}"
      },
      "severity": "${latestEvent.severity}",
      "deepLink": "${latestEvent.deepLink}"
    }
  }
  ```

* Response Handling Criteria:
  * Success Criteria: Status Code 200
* Settings:
  * One Request Per Event: Enabled

After setting up a template, create a new action in AppDynamics and select the template you created earlier.
Now you can configure policies to trigger the action when certain events occur in AppDynamics.
When configuring a policy, select the following events to trigger the action:

```plain
Health Rule Violation Started - Warning
Health Rule Violation Started - Critical
Health Rule Violation Continues - Warning
Health Rule Violation Continues - Critical
Health Rule Violation Upgraded - Warning to Critical
Health Rule Violation Downgraded - Critical to Warning
Health Rule Violation Ended - Warning
Health Rule Violation Ended - Critical
Health Rule Violation Canceled - Warning
Health Rule Violation Canceled - Critical
```

After setting up the connection, you can test it by sending a test request from the AppDynamics UI.

## Understanding How Alerts Grouped and Auto-resolved

Grafana OnCall provides grouping and auto-resolve logic for the AppDynamics integration:

* Alerts created from health rule violation events are grouped by application and node name
* Alert groups are auto-resolved when the health rule violation is ended or canceled

## Complete the Integration Configuration

Complete configuration by setting routes, templates, maintenances, etc. Read more in
[this section][complete-the-integration-configuration]

{{% docs/reference %}}
[complete-the-integration-configuration]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/integrations#complete-the-integration-configuration"
[complete-the-integration-configuration]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/integrations#complete-the-integration-configuration"

[user-and-team-management]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
[user-and-team-management]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/user-and-team-management"
{{% /docs/reference %}}
