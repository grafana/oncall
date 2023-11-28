---
canonical: https://grafana.com/docs/oncall/latest/escalation-chains-and-routes/
title: Escalation Chains and Routes
weight: 600
---

# Escalation Chains and Routes

Often alerts from monitoring systems need to be sent to different escalation chains and messaging channels, based on their severity, or other alert content.

## Routes

Routes are used to determine which escalation chain should be used for a specific alert
group. A route's ["Routing Templates"][routing-template]
are evaluated for each alert and **the first matching route** is used to determine the
escalation chain and chatops channels.

> **Example:**
>
>
> * trigger escalation chain called `Database Critical` for alerts with `{{ payload.severity == "critical" and payload.service == "database" }}` in the payload
> * create a different route for alerts with the payload `{{ "synthetic-monitoring-dev-" in payload.namespace }}` and select a escalation chain called `Security`.

### Manage routes

1. Open Integration page
2. Click **Add route** button to create a new route
3. Click **Edit** button to edit `Routing Template`. The routing template must evaluate to `True` for it to apply
4. Select channels in **Publish to Chatops** section
   > **Note:** If **Publish to Chatops** section does not exist, connect Chatops integrations first, see more in [docs][notify]
5. Select **Escalation Chain** from the list
6. If **Escalation Chain** does not exist, click **Add new escalation chain** button to create a new one, it will open in a new tab.
7. Once created, **Reload list**, and select the new escalation chain
8. Click **Arrow Up** and **Arrow Down** on the right to change the order of routes
9. Click **Three dots** and **Delete Route** to delete the route

## Escalation Chains

Once an alert group is created and assigned to the route with escalation chain, the
escalation chain will be executed. Until user performs an action, which stops the escalation
chain (e.g. acknowledge, resolve, silence etc), the escalation chain will continue to
execute.

Users can create escalation chains to configure different type of escalation workflows.
For example, you can create a chain that will notify on-call users with high priority, and
another chain that will only send a message into a Slack channel.

Escalation chains determine Who and When to notify. [How to notify][notify] is set by the user, based on their own preferences.

### Types of escalation steps

* `Wait` - wait for a specified amount of time before proceeding to the next step. If you
need a larger time interval, use multiple wait steps in a row.
* `Notify users` - send a notification to a user or a group of users.
* `Notify users from on-call schedule` - send a notification to a user or a group of users
from an on-call schedule.
* `Resolve incident automatically` - resolve the alert group right now with status
`Resolved automatically`.
* `Notify whole slack channel` - send a notification to the users in the slack channel.
* `Notify Slack User Group` - send a notification to each member of a slack user group.
* `Trigger outgoing webhook` - trigger an [outgoing webhook][outgoing-webhooks].
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
their [respective policies]([url](https://grafana.com/docs/oncall/latest/notify/#configure-user-notification-policies)).

### Notification types

Each escalation step that notifies a user, does so by triggering their personal notification steps. These are configured in the Grafana
 OnCall users page (by clicking "View my profile").
It will be executed for each user in the escalation step
User can configure two types of personal notification chains:

* **Default Notifications**

* **Important Notifications**

In the escalation step, user can select which type of notification to use.

Check more information on [Personal Notification Preferences][notify] page.

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
[notify]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/notify"
[notify]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/notify"

[outgoing-webhooks]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/outgoing-webhooks"
[outgoing-webhooks]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/outgoing-webhooks"

[routing-template]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/jinja2-templating#routing-template"
[routing-template]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/jinja2-templating#routing-template"
{{% /docs/reference %}}
