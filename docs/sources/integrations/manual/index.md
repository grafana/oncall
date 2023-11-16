---
aliases:
  - /docs/oncall/latest/integrations/manual/
canonical: https://grafana.com/docs/oncall/latest/integrations/manual/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - Alertmanager
  - Prometheus
  - Direct paging
title: Page people manually
weight: 300
---

# Page people manually

Grafana OnCall relies on automated and pre-configured workflows, such as [integrations][integrations],
[routes, and escalation chains][escalation-chains-and-routes] to handle most of the incident response process.
However, sometimes you might need to page a [team][manage-teams] or request assistance from specific people that
are not part of these pre-defined rules.

For such ad-hoc scenarios, Grafana OnCall allows you to create an alert group, input necessary information, and decide
who will be alerted – a team, or a set of users.

## Page a team

Click on **+ Escalation** on the **Alert groups** page to start creating a new alert group.
From there, you can configure the alert group to notify a particular team and optionally include additional users. Here are the inputs you need to fill in:

- **Message**: Write a message to provide more details or instructions to those whom you are paging.
- **Team**: Select the team you want to page. The team's
  [direct paging integration](#learn-the-flow-and-handle-warnings) will be used for notification. _Note_ that you will only
  see teams that have a "contactable" direct paging integration (ie. it has an escalation chain assigned to it, or has
  at least one Chatops integration connected to send notifications to).
- **Users**: Include more users to the alert group. For each additional user, you can select a notification policy:
  [default or important][notify].

> The same feature is also available as [**/escalate**][slack-escalate] Slack command.

## Add users to an existing alert group

If you want to page more people for an existing alert group, you can do so using the **+ Add**
button, within the "Participants" section on the specific alert group's page. The same functionality is available in
Slack using the **Responders** button in the alert group's message.

Notifying additional users doesn't disrupt or interfere with the escalation chain configured for the alert group;
it simply adds more responders and notifies them immediately. Note that adding users for an existing alert group
will page them even if the alert group is silenced or acknowledged, but not if the alert group is resolved.

> It's not possible to page a team for an existing alert group. To page a specific team, you need to
> [create a new alert group](#page-a-team).

## Learn the flow and handle warnings

When you pick a team to page, Grafana OnCall will automatically use the right direct paging integration for the team.
"Direct paging" is a special kind of integration in Grafana OnCall that is unique per team and is used to send alerts
to the team's ChatOps channels and start an appropriate escalation chain.

## Set up direct paging for a team

By default all teams will have a direct paging integration created for them. However, these are not configured by default.
If a team does not have their direct paging integration configured, such that it is "contactable" (ie. it has an
escalation chain assigned to it, or has at least one Chatops integration connected to send notifications to), you will
not be able to direct page this team. If this happens, consider following the following steps for the team (or reach out
to the relevant team and suggest doing so).

Navigate to the **Integrations** page and find the "Direct paging" integration for the team in question. From the
integration's detail page, you can customize its settings, link it to an escalation chain, and configure associated
ChatOps channels. To confirm that the integration is functioning as intended, [create a new alert group](#page-a-team)
and select the same team for a test run.

{{% docs/reference %}}
[integrations]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/integrations"
[integrations]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/integrations"

[escalation-chains-and-routes]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/escalation-chains-and-routes"
[escalation-chains-and-routes]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/escalation-chains-and-routes"

[notify]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/notify#configure-user-notification-policies"
[notify]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/notify#configure-user-notification-policies"

[slack-escalate]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/notify/slack#slack-escalate-command"
[slack-escalate]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/notify/slack#slack-escalate-command"

[manage-teams]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management#manage-teams-in-grafana-oncall"
[manage-teams]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/user-and-team-management#manage-teams-in-grafana-oncall"
{{% /docs/reference %}}
