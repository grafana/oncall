---
title: Manual paging
menuTitle: Manual paging
description: Manually page people in Grafana OnCall.
weight: 0
keywords:
  - OnCall
  - Integrations
  - Alerts
  - Direct paging
  - Notifications
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/references/appdynamics
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/manual
  - /docs/grafana-cloud/alerting-and-irm/oncall/integrations/manual
  - /docs/oncall/latest/integrations/manual/
  - ../integrations/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/manual
refs:
  integrations:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/integrations/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/
  notify:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/notify/#configure-user-notification-policies
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/notify/#configure-user-notification-policies
  manage-teams:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/user-and-team-management/#manage-teams-in-grafana-oncall
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/user-and-team-management/#manage-teams-in-grafana-oncall
  slack-escalate:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/notify/slack/#slack-escalate-command
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/notify/slack/#slack-escalate-command
  escalation-chains-and-routes:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/escalation-chains-and-routes/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/escalation-chains-and-routes/
---

# Page people manually

Grafana OnCall relies on automated and pre-configured workflows, such as [integrations](ref:integrations),
[routes, and escalation chains](ref:escalation-chains-and-routes) to handle most of the incident response process.
However, sometimes you might need to page a [team](ref:manage-teams) or request assistance from specific people that
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
  [default or important](ref:notify).

> The same feature is also available as [**/escalate**](ref:slack-escalate) Slack command.

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

By default all teams will have a direct paging integration created for them. Each direct paging integration will be
created with two routes:

- a non-default route which has a Jinja2 filtering term of `{{ payload.oncall.important }}`
(see [Important Escalations](#important-escalations) below for more details)
- a default route to capture all other alerts

However, these integrations are not configured by default to be "contactable" (ie. their routes will have no
escalation chains assigned to them, nor any Chatops integrations connected to send notifications to).
If a team does not have their direct paging integration configured, such that it is "contactable" , you will
not be able to direct page this team. If this happens, consider following the following steps for the team (or reach out
to the relevant team and suggest doing so).

Navigate to the **Integrations** page and find the "Direct paging" integration for the team in question. From the
integration's detail page, you can customize its settings, link it to an escalation chain, and configure associated
ChatOps channels. To confirm that the integration is functioning as intended, [create a new alert group](#page-a-team)
and select the same team for a test run.

### Important escalations

Sometimes you really need to get the attention of a particular team. When directly paging a team, it is possible to
page them using an "important escalation". Practically speaking, this will create an alert, using the specified team's
direct paging integration as such:

```json
{
    "oncall": {
        "title": "IRM is paging Network team to join escalation",
        "message": "I really need someone from your team to come take a look! The k8s cluster is down!",
        "uid": "8a20b8d1-56fd-482e-824e-43fbd1bd7b10",
        "author_username": "irm",
        "permalink": null,
        "important": true
    }
}
```

When you are directly paging a team, either via the web UI, chatops apps, or the API, you can specify that this
esclation be "important", which will effectively set the value of `oncall.important` to `true`. As mentioned above in
[Set up direct paging for a team](#set-up-direct-paging-for-a-team), direct paging integrations come pre-configured with
two routes, with the non-default route having a Jinja2 filtering term of `{{ payload.oncall.important }}`.

This allows teams to be contacted via different escalation chains, depending on whether or not the user paging them
believes that this is an "important escalation".
