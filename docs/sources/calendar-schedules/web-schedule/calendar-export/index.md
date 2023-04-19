---
canonical: https://grafana.com/docs/oncall/latest/calendar-schedules/web-schedule/calendar-export/
description: Learn how to export an on-call schedule from Grafana OnCall
keywords:
  - Grafana
  - oncall
  - on-call
  - calendar
  - iCal export
title: Export on-call schedules
weight: 500
---

# Export on-call schedules

Export on-call schedules from Grafana OnCall to your preferred calendar app with a one-time secret iCal URL.
The schedule export allows you to add on-call schedules to your existing calendar to view on-call shifts alongside the
rest of your schedule.  

There are two schedule export options available:

- **On-call schedule export** - Exports all on-call shifts for a particular schedule, including rotations, overrides,
and assigned users.
- **User-specific schedule export** - Exports assigned on-call shifts for a particular user. Use this export option to
add your assigned on-call shifts to your calendar.

> **Note:** Calendar exports include all scheduled shifts, including those which are lower priority or overridden.

## Export an on-call schedule

Use this export option to add all on-call shifts associated with a schedule to a calendar. Best for a team or shared
calendars.

To export a schedule from Grafana OnCall:

1. In Grafana OnCall, navigate to the **Schedules** tab.
1. Open the schedule you’d like to export by clicking on the schedule name.
1. Click **Export** in the upper right corner, then click **+ Create iCal link** to generate a secret iCal URL.
1. Copy the iCal link and store it somewhere you’ll remember. Once you close the schedule export window, you won't be
able to access the iCal link.
1. Open your calendar settings to add a calendar from a URL (This step varies based on your calendar app).

## Export a user on-call schedule

Use this export option to add your assigned on-call shifts to your calendar. Best for personal calendars.

To export your on-call schedule:

1. In Grafana OnCall, navigate to the **Users** tab.
1. Click **View my profile** in the upper right corner.
1. From the **User Info** tab, navigate to the iCal link section.
1. Click **+ Create iCal link** to generate your secret iCal URL.
1. Copy the iCal link and store it somewhere you’ll remember. Once you close your user profile, you won't be able to
access the iCal link again.
1. Open your calendar settings to add a calendar from a URL (This step varies based on your calendar app).

## Revoke an iCal export link

iCal links are displayed upon creation, and users are advised to copy their link and store it for future reference.
To ensure the security of your and your teams' calendar data, after an iCal link is generated, the link is hidden and
cannot be accessed again.

If you need to revoke an iCal link, you can do so anytime. By doing so, any calendar that references the revoked link
will lose access to the calendar data.

To revoke an active iCal link:

1. Navigate to the schedule or user profile associated with the iCal link.
1. For schedules, click **Export** to open the Schedule export window.
1. For users, navigate to the iCal link section of the **User info** tab.
1. If there is an active iCal link, click **Revoke iCal link**.
1. Once revoked, you can generate a new iCal link by clicking **+ Create iCal link**.
