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
---

# Escalation Chains and Routes

Often alerts from monitoring systems need to be sent to different escalation chains and messaging channels, based on their severity, or other alert content.

## Routes

Routes are used to determine which escalation chain should be used for a specific alert
group. A route's _[Routing Templates]_
are evaluated for each alert and **the first matching route** is used to determine the
escalation chain and chatops channels.

> **Example:**
>
>
> * trigger escalation chain called `Database Critical` for alerts with `{{ payload.severity == "critical" and payload.service == "database" }}` in the payload
> * create a different route for alerts with the payload `{{ "synthetic-monitoring-dev-" in payload.namespace }}` and select a escalation chain called `Security`.

### Manage routes

1. Open Integration page
1. Click **Add route** button to create a new route
1. Click **Edit** button to edit `Routing Template`. The routing template must evaluate to `True` for it to apply
1. Select channels in **Publish to Chatops** section
   > **Note:** If the **Publish to Chatops** section doesn't exist, connect Chatops integrations first.
   > For more information, refer to [Notify people].
1. Select **Escalation Chain** from the list
1. If **Escalation Chain** does not exist, click **Add new escalation chain** button to create a new one, it will open in a new tab.
1. Once created, **Reload list**, and select the new escalation chain
1. Click **Arrow Up** and **Arrow Down** on the right to change the order of routes
1. Click **Three dots** and **Delete Route** to delete the route

### Routing based on labels

> **Note:** Labels are currently available only in cloud.

In addition, there is a `labels` variable available to your routing templates, which contains all of the labels assigned
to the Alert Group, as a `dict`. This allows you to route based on labels (or a mix of labels and/or payload based data):

> **Example:**
>
> * `{{ labels.foo == "bar" or "hello" in labels.keys() or payload.severity == "critical" }}`

## Escalation Chains

Once an alert group is created and assigned to the route with escalation chain, the
escalation chain will be executed. Until user performs an action, which stops the escalation
chain (e.g. acknowledge, resolve, silence etc), the escalation chain will continue to
execute.

Users can create escalation chains to configure different type of escalation workflows.
For example, you can create a chain that will notify on-call users with high priority, and
another chain that will only send a message into a Slack channel.

Escalation chains determine Who and When to notify. How to notify is set by the user, based on their own preferences.

### Types of escalation steps

* `Wait` - wait for a specified amount of time before proceeding to the next step. If you
need a larger time interval, use multiple wait steps in a row.
* `Notify users` - send a notification to a user or a group of users.
* `Notify users from on-call schedule` - send a notification to a user or a group of users
from an on-call schedule.
* `Notify all users from a team` - send a notification to all users in a team.
* `Resolve incident automatically` - resolve the alert group right now with status
`Resolved automatically`.
* `Notify whole slack channel` - send a notification to the users in the slack channel. These users will be notified
via the method configured in their user profile.
* `Notify Slack User Group` - send a notification to each member of a slack user group. These users will be notified
via the method configured in their user profile.
* `Trigger outgoing webhook` - trigger an [outgoing webhook].
* `Notify users one by one (round robin)` - each notification will be sent to a group of
users one by one, in sequential order in [round robin fashion](https://en.wikipedia.org/wiki/Round-robin_item_allocation).
* `Continue escalation if current time is in range` - continue escalation only if current
time is in specified range. It will wait for the specfied time to continue escalation.
Useful when you want to get escalation only during working hours
* `Continue escalation if >X alerts per Y minutes (beta)` - continue escalation only if it
passes some threshold
* `Repeat escalation from beginning (5 times max)` - loop the escalation chain

> **Note:** Both "**Notify whole Slack channel**" and "**Notify Slack User Group**" will filter OnCall registered users
matching the users in the Slack channel or Slack User Group with their profiles linked to their Slack accounts (ie. users
should have linked their Slack and OnCall users). In both cases, the filtered users satisfying the criteria above are
notified following their respective notification policies. However, to avoid **spamming** the Slack channel/thread,
users **won't be notified** in the alert group Slack **thread** (this is how the feature is currently implemented)
but instead notify them using their **other defined** options in
their respective policies.

### Notification types

Each escalation step that notifies a user, does so by triggering their personal notification steps. These are configured in the Grafana
 OnCall users page (by clicking "View my profile").
It will be executed for each user in the escalation step
User can configure two types of personal notification chains:

* **Default Notifications**

* **Important Notifications**

In the escalation step, user can select which type of notification to use.
For more information, refer to [Notify people].

### Manage Escalation Chains

1. Open **Escalation Chains** page
2. Click **New escalation chain** button to create a new escalation chain

3. Enter a name and assign it to a team
   > **Note:** Name must be unique across organization
   > **Note:** Alert Groups inherit the team from the Integration, not the Escalation Chain
4. Click **Add escalation step** button to add a new step
5. Click **Delete** to delete the Escalation Chain, and **Edit** to edit the name or the team.

> **Important:** Linked Integrations and Routes are displayed in the right panel. Any change in the Escalation Chain will
affect all linked Integrations and Routes.

{{% docs/reference %}}
[Notify people]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/manage/notify"
[Notify people]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/manage/notify"

[outgoing webhook]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/outgoing-webhooks"
[outgoing webhook]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/outgoing-webhooks"

[Routing Templates]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/integrations#routing-template"
[Routing Templates]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/integrations#routing-template"
{{% /docs/reference %}}
