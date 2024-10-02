---
title: Escalation chains and routes
menuTitle: Escalation chains and routes
description: Understand how to configure escalation chains and routes for OnCall.
weight: 300
keywords:
  - OnCall
  - Configuration
  - Routes
  - Escalation
  - Alert templates
  - Routing template
  - Notify
canonical: https://grafana.com/docs/oncall/latest/configure/escalation-chains-and-routes/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/escalation-chains-and-routes/
  - /docs/grafana-cloud/alerting-and-irm/oncall/escalation-chains-and-routes/
  - ../escalation-chains-and-routes/ # /docs/oncall/<ONCALL_VERSION>/escalation-chains-and-routes/
refs:
  notify-people:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/notify/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/notify/
  routing-templates:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating/#routing-template
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating/#routing-template
  outgoing-webhook:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/integrations/outgoing-webhooks/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/outgoing-webhooks/
---

# Escalation Chains and Routes

In Grafana OnCall, configuring proper alert routing and escalation ensures that alerts are directed to the right teams and handled promptly.

Alerts often need to be sent to different teams or channels depending on their severity or specific alert details.
Set up routes and escalation chains to customize and automate escalation according to each teams workflows.

## Routes

Routes determine which escalation chain should be triggered for a specific alert group based on the details of the alert.
A route uses [Routing Templates](ref:routing-templates) to determine the escalation chain and notification channels.

When an alert is received, its details are evaluated against the route's routing template, and **the first matching route** determines how the alert will be handled.

**Example:**

- Trigger the `Database Critical` escalation chain for alerts with `{{ payload.severity == "critical" and payload.service == "database" }}`
- Use a different route for alerts with the payload `{{ "synthetic-monitoring-dev-" in payload.namespace }}`, selecting the `Security` escalation chain.

### Create and manage routes

To create or manage a route:

1. Navigate to the **Integrations** page.
1. Click **Add route** to create a new route, or **Edit** to modify an existing one.
1. In the **Routing Template** section, define conditions that will determine which alerts this route applies to.
The template must evaluate to `True` for the route to be selected.
1. Select the appropriate escalation chain from the **Escalation Chain** dropdown.
If an escalation chain doesn’t exist, click **Add new escalation chain**, which will open a new tab for chain creation.
After creating the chain, return to the routes page and click **Reload list** to update the available options.
1. In the **Publish to ChatOps** section, select the relevant communication channels for this route (Slack, Teams, etc.).
Ensure ChatOps integrations are configured before using this feature.
1. Arrange the routes by clicking the up/down arrows to prioritize the routes as needed. The order determines which route is evaluated first.
1. To delete a route, click the three dots on the route and select **Delete Route**.

### Label-based routing

{{< admonition type="note" >}}
This feature is available exclusively on Grafana Cloud.
{{< /admonition >}}

You can use the labels variable in your routing templates to evaluate based on alert group labels.
This provides additional flexibility in routing alerts based on both labels and payload data.

**Example:**

`{{ labels.foo == "bar" or "hello" in labels.keys() or payload.severity == "critical" }}`

## Escalation Chains

Escalation chains define the series of actions taken when an alert is triggered.
The chain continues until a user intervenes by acknowledging, resolving, or silencing the alert.

You can configure different escalation chains for different workflows.
For example, one chain might notify on-call users immediately, while another sends a low-priority message to a Slack channel.

### Create and manage escalation chains

1. Navigate to the **Escalation Chains** page.
1. Click **New escalation chain** to create a new chain.
1. Enter a unique name and assign the chain to a team.
1. Click **Add escalation step** to define the steps for this chain (e.g., notifying users, waiting, escalating).
1. To edit an existing chain, click **Edit**. To remove a chain, click **Delete**.

{{< admonition type="note" >}}

- The name must be unique across the organization.
Alert groups inherit the team from the integration, not the escalation chain.
- Linked integrations and routes are shown in the right panel.
Changes to the escalation chain impact all associated integrations and routes.
{{< /admonition >}}

### Types of escalation steps

- `Wait`: Pause for a specified time before moving to the next step. You can add multiple wait steps for longer intervals.
- `Notify users`: Notify individual users or groups.
- `Notify users from on-call schedule`: Send notifications to users from a defined on-call schedule.
- `Notify all team members`: Notify all users in a team.
- `Resolve incident automatically`: Immediately resolve the alert group with the status `Resolved automatically`.
- `Notify Slack channel members`: Notify users in a Slack channel based on their OnCall profile preferences.
- `Notify Slack user group`: Notify all members of a Slack user group.
- `Trigger outgoing webhook`: Activate an [outgoing webhook](ref:outgoing-webhooks).
- `Round robin notifications`: Notify users sequentially, with each user receiving different alert groups.
- `Time-based escalation`: Continue escalation only if the current time falls within a specific range (e.g., during working hours)
- `Threshold-based escalation`: Escalate only if a certain number of alerts occur within a specific time frame.
- `Repeat escalation`: Loop the escalation chain up to five times.
- `Declare incident (non-default routes)`: **Available only in Grafana Cloud**. Declares an incident with a specified severity.
Limited to one incident per route at a time.
Additional alerts are grouped into the active incident, and up to five are listed as incident context.

{{< admonition type="note" >}}
The **Notify Slack channel members** and **Notify Slack user group** steps are designed to notify OnCall-registered users via their configured notification rules.
To avoid spamming a Slack channel with alert group notifications, notifications are not sent in the alert group Slack thread.
{{< /admonition >}}

### Notification types

When an escalation step notifies a user, it follows their personal notification settings, which are configured in their user profile.

Each user can have two sets of notification rules:

- **Default Notifications**: For standard alerts.
- **Important Notifications**: For high-priority alerts.

Each escalation step allows you to select which set of notification rules to use.
For more information about user notification rules, refer to the [Notifications](ref:notify-people) section.
