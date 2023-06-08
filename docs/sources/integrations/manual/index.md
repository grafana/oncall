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
title: Raising alerts manually
weight: 300
---

# Raising alerts manually

Sometimes you need to page a specific person (following their preferred notification policy), or need help from people
in some particular team. In that case you can trigger an alert group providing some context information as well as
defining who to notify about it, a user or the person on-call in a given team's schedule.

You can create a manual alert group using the "+ Manual alert group" button (in the Alert Groups page), and set
its escalation options to page a specific person or group of people.

> The same feature is also available as **/escalate** slack command.

- You need to define a title for your alert, an optional description, and select the responders which could be a
specific user in your team, a particular schedule, or multiple instances of those.
- When selecting a user, a few checks will be performed before adding them to the list of responders: user should have
a notification policy set, and ideally be on-call.
- If the user is not on-call at the time, you will get alternative users to choose instead from the OnCall schedules
that user is part of. You can still page the original user if you confirm that is what you want.
- When selecting a schedule, the user(s) on-call when the alert is triggered will be notified.

> **NOTE:** for each responder (user or schedule) you can choose the notification policy to use: default or important.
