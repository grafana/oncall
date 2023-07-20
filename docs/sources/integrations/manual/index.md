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
However, sometimes you might need to page a team or request assistance from specific people that are not part of
these pre-defined rules.

For such ad-hoc scenarios, Grafana OnCall allows you to create an alert group, input necessary information, and decide
who will be alerted – a team, a user, or an on-call user from a specific schedule.

## Page a team

Click on "+ New alert group" on the "Alert groups" page to start creating a new alert group.
From there, you can configure the alert group to notify a particular team and optionally include additional users or
schedules. Here are the inputs you need to fill in:

- **Title**: Write a brief and clear title for your alert group.
- **Message**: Optionally, add a message to provide more details or instructions.
- **Team**: Select the team you want to page. The team's
[direct paging integration](#learn-the-flow-and-handle-warnings) will be used for notification.
- **Additional Responders**: Optionally, include more responders for the alert group.
These could be any combination of users and schedules.
For each additional responder (user or schedule), you can select a notification policy: [default or important][notify].

> The same feature is also available as [**/escalate**][slack-commands] Slack command.

## Add responders for an existing alert group

If you want to page more people for an existing alert group, you can do so using the "Notify additional responders"
button on the specific alert group's page. Here you can select more users, or choose users who are on-call for specific
schedules. The same functionality is available in Slack using the "Responders" button in the alert group's message.

Notifying additional responders doesn't disrupt or interfere with the escalation chain configured for the alert group;
it simply adds more responders and notifies them immediately.

> It's not possible to page a team for an existing alert group. To page a specific team, you need to
[create a new alert group](#page-a-team).

## Learn the flow and handle warnings

When you pick a team to page, Grafana OnCall will automatically use the right direct paging integration for the team.
"Direct paging" is a special kind of integration in Grafana OnCall that is unique per team and is used to send alerts
to the team's ChatOps channels and start an appropriate escalation chain.

If a team hasn't set up a direct paging integration, or if the integration doesn't have any escalation chains connected,
Grafana OnCall will issue a warning. If this happens, consider
[setting up a direct paging integration](#set-up-direct-paging-for-a-team) for the team
(or reach out to the relevant team and suggest doing so).

## Set up direct paging for a team

To create a direct paging integration for a team, click "+ New alert group" on the "Alert groups" page, choose the team,
and create an alert group, **regardless of any warnings**. This action automatically triggers Grafana OnCall to generate
a [direct paging integration](#learn-the-flow-and-handle-warnings) for the chosen team.

After setting up the integration, you can customize its settings, link it to an escalation chain,
and configure associated ChatOps channels.
To confirm that the integration is functioning as intended, [create a new alert group](#page-a-team)
and select the same team for a test run.

{{% docs/reference %}}
[integrations]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/integrations"
[integrations]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/integrations"

[escalation-chains-and-routes]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/escalation-chains-and-routes"
[escalation-chains-and-routes]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/escalation-chains-and-routes"

[notify]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/notify#configure-user-notification-policies"
[notify]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/notify#configure-user-notification-policies"

[slack-commands]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/notify/slack#slack-commands"
[slack-commands]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/notify/slack#slack-commands"
{{% /docs/reference %}}
