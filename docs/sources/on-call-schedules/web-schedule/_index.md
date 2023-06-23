---
title: Web-based on-call schedules
canonical: https://grafana.com/docs/oncall/latest/on-call-schedules/web-schedule/
description: "Learn more about Grafana OnCalls built in schedule tool"
keywords:
  - Grafana
  - oncall
  - schedule
  - calendar
title: Web-based schedules
weight: 100
---

# Web-based on-call schedules

Grafana OnCall allows you to map out recurring on-call coverage and automate the escalation of alert notifications to
on-call users. Configure and manage on-call schedules directly in the Grafana OnCall plugin to easily customize
rotations with a live schedule preview, reference teammates' time zones, and add overrides.

<iframe width="560" height="315" src="https://www.youtube.com/embed/ESkS26SesWk" title="YouTube video player"
frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture;
web-share" allowfullscreen></iframe>

This topic provides an overview of key components and features.

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

## Schedule quality report

The schedule view features a quality report that provides a score for your schedule based on rotations and overrides.
It's calculated based on these key factors:

- Gaps (amount of time when no one is on-call)
- Balance (uneven distribution of on-call shifts between team members)

Quality score is a numeric value between 0 and 100. The higher the score, the better the schedule quality.
Web UI uses the following scale to show the quality score:

- 0-20: Bad
- 20-40: Low
- 40-60: Medium
- 60-80: Good
- 80-100: Great

To improve quality score:

- Minimize the amount of time when no one is on-call.
- Ensure users in the schedule have a similar amount of on-call time.

Depending on the quality score, the report can also provide:

- Percentage of time when no one is on-call. E.g. "29% not covered" means that 29% of the time no one is on-call for
the schedule. 24/7/365 coverage is considered ideal, so reducing this number will improve the overall schedule quality.
- List of overloaded users. A user is considered overloaded if they have more on-call time than average for the schedule.
E.g. "+15% avg" in quality report means that user has 15% more on-call time than average for the schedule.
A perfectly balanced schedule is considered ideal, so reducing this number will improve the overall schedule quality.

>**Note**: The next 52 weeks (~1 year) are taken into account when generating the quality report.

## Schedule export

Export on-call schedules from Grafana OnCall to your preferred calendar app with a one-time secret iCal URL. The
schedule export allows you to view on-call shifts alongside the rest of your schedule.
