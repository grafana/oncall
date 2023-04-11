---
aliases:
  - /docs/oncall/latest/escalation-policies/configure-routes/
canonical: https://grafana.com/docs/oncall/latest/escalation-policies/configure-routes/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - amixr
  - oncall
  - integrations
title: Configure and manage routes
weight: 300
---

# Configure and manage Routes

Set up escalation chains and routes to configure escalation behavior for alert group notifications.

## Configure escalation chains

You can create and edit escalation chains in two places: within **Integrations**, by clicking on an integration tile,
and in **Escalation Chains**. The following steps are for the **Integrations** workflow, but are generally applicable
in both situations.

You can use **escalation chains** and **routes** to determine ordered escalation procedures. Escalation chains allow
you to set up a series of alert group notification actions that trigger if certain conditions that you specify are
met or not met.

1. Click on the integration tile for which you want to define escalation policies.

   The **Escalations** section for the notification is in the pane to the right of the list of notifications.
   You can click **Change alert template and grouping** to customize the look of the alert. You can also do this by
   clicking the **Settings** (gear) icon in the integration tile.

1. Create an escalation chain.

   In the escalation pane, click **Escalate to** to choose from previously added escalation chains, or create a new one
   by clicking **Make a copy** or **Create a new chain**. This will be the name of the escalation policy you define.

1. Add escalation steps.

   Click **Add escalation step** to choose from a set of actions and specify their triggering conditions. By default, the
   first step is to notify a slack channel or user. Specify users or channels or toggle the switch to turn this step off.

   To mark an escalation as **Important**, select the option from the step **Start** dropdown menu. User notification
   policies can be separately defined for **Important** and **Default** escalations.

## Create a route

To add a route, click **Add Route**.

You can set up a single route and specify notification escalation steps, or you can add multiple routes, each with
its own configuration.

Each route added to an escalation policy follows an `IF`, `ELSE IF`, or `ELSE` path and depends on the type of alert you
specify using a Jinja template that matches content in the payload body of the first alert in alert group. You can also
specify where to send the notification for each route.

For example, you can send notifications for alerts with `{{ payload.severity == "critical" and payload.service ==
"database" }}` in the payload to an escalation chain called `Bob_OnCall`. You can create a different route for alerts
with the payload `{{ "synthetic-monitoring-dev-" in payload.namespace }}` and select a escalation chain called
`NotifySecurity`.

Alternatively you can use regular expressions, e.g. `\"severity\": \"critical\"` or `\"namespace\" *:
*\"synthetic-monitoring-dev-.*\"`

You can set up escalation steps for each route in a chain.

> **NOTE:** When you modify an escalation chain or a route, it will modify that escalation chain across
> all integrations that use it.
