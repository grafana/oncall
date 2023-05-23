---
title: Web-based on-call schedules
aliases:
  - /docs/oncall/latest/on-call-schedules/web-schedule/
canonical: https://grafana.com/docs/oncall/latest/on-call-schedules/web-schedule/
description: "Learn more about Grafana OnCalls built in schedule tool"
keywords:
  - Grafana
  - oncall
  - schedule
  - calendar
weight: 100
---

# NOT EDITED AFTER STRUCTURE CHANGE

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

Schedules allow you to map out recurring on-call coverage and automate the escalation of alert notifications to
currently on-call users. With Grafana OnCall, you can customize rotations with a live schedule preview to visualize
your schedule, add users, reorder users, and reference teammates' time zones.

To learn more, see [On-call schedules]({{< relref "../../../calendar-schedules" >}}) which provides the fundamental
concepts for this task.

## Before you begin

- Users with Admin or Editor roles can create, edit and delete schedules.
- Users with Viewer role cannot receive alert notifications, therefore, cannot be on-call.

For more information about permissions, refer to
[Manage users and teams for Grafana OnCall]({{< relref "../../../configure-user-settings" >}})

## Create an on-call schedule

To create a new on-call schedule:

1. In Grafana OnCall, navigate to the **Schedules** tab and click **+ New schedule**
1. Navigate to **Set up on-call rotation schedule** and click **+ Create**
1. Provide a name and review available schedule settings
1. When you’re done, click **Create Schedule**

>**Note:** You can edit your schedule settings at any time.

### Add a rotation to your on-call schedule

After creating your schedule, you can add rotations to build out your coverage needs.
Think of a rotation as a recurring schedule containing on-call shifts that users rotate through.

To add a rotation to an on-call schedule:

1. From your newly created schedule, click **+ Add rotation** and select **New Layer**.
1. Complete the rotation creation form according to your rotation parameters.
1. Add users to the rotation from the dropdown.
You can separate users into user groups to rotate through individual users per shift.
User groups that contain
multiple users results in all users in the group being included in corresponding shifts.
1. When you’re satisfied with the rotation preview, click **Create**.

### Add an on-call schedule to escalation chains

Now that you’ve created your schedule, it must be referenced in the steps of an escalation chain for on-call users
to receive alert notifications.

To connect a schedule to an escalation chain:

1. In Grafana OnCall, go to the **Escalation Chains** tab.
1. Navigate to an existing escalation chain or click **+ New Escalation Chain**.
1. Select **Notify users from on-call schedule** from the **Add escalation step** dropdown.
1. Specify which notification policy to use and the appropriate schedule.
1. Click and drag the escalation steps to reorder, if needed.

Escalation chain steps are saved automatically.

For more information about Escalation Chains, refer to
[Configure and manage Escalation Chains]({{< relref "../../../escalation-policies/configure-escalation-chains" >}})
