---
canonical: https://grafana.com/docs/oncall/latest/calendar-schedules/web-schedule/
description: Learn more about Grafana OnCalls built in schedule tool
keywords:
  - Grafana
  - oncall
  - schedule
  - calendar
title: Web-based schedules
weight: 100
---

# About web-based schedules

Grafana OnCall allows you to map out recurring on-call coverage and automate the escalation of alert notifications to
on-call users. Configure and manage on-call schedules directly in the Grafana OnCall plugin to easily customize
rotations with a live schedule preview, reference teammates' time zones, and add overrides.

This topic provides an overview of key components and features.

For information on how to create a schedule in Grafana OnCall, refer to
[Create an on-call schedule]({{< relref "create-schedule" >}})

>**Note**: User permissions determine which components of Grafana OnCall are available to you.

## Schedule settings

Schedule settings are initially configured when a new schedule is created and can be updated at any time by clicking
the gear icon next to an existing schedule.

Available schedule settings:

- **Slack channel:** Choose a primary Slack channel to send notifications about on-call shifts, such as unassigned on-call shifts.
- **Slack user group:** Choose a Slack user group to receive current on-call updates.
- **Notification frequency:** Specify whether or not to send shift notifications to scheduled team members.
- **Action for slot when no one is on-call:** Define how your team is notified when an empty shift causes a gap in on-call coverage.
- **Current shift notification settings:** Select how users are notified when their on-call shift begins.
- **Next shift notification settings:** Specify how users are notified of upcoming shifts.

## Schedule view

The schedule view is a detailed calendar representation of your on-call schedule. It contains three interactive weekly
calendars and a 24-hour on-call status bar for visualizing who’s on-call and what time it is for your teammates.

Understand your schedule view:

- **Final schedule:** The final schedule provides a combined view of rotations and overrides
- **Rotations:** The rotations calendar represents all recurring on-call rotations for a given schedule.
- **Overrides:** The override calendar represents temporary adjustments to the recurring on-call schedule. Any events
on this calendar will take precedence over the rotations calendar.

## Schedule export

Export on-call schedules from Grafana OnCall to your preferred calendar app with a one-time secret iCal URL. The
schedule export allows you to view on-call shifts alongside the rest of your schedule.  

For more information, refer to [Export on-call schedules]({{< relref "calendar-export" >}})
