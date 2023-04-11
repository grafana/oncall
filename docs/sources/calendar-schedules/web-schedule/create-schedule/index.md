---
title: Create on-call schedules
aliases:
  - /docs/oncall/latest/calendar-schedules/web-schedule/create-schedule/
canonical: https://grafana.com/docs/oncall/latest/calendar-schedules/web-schedule/create-schedule/
description: "Create on-call schedules with Grafana OnCall"
keywords:
  - Grafana
  - oncall
  - on-call
  - schedule
  - calendar
weight: 300
---

# Create on-call schedules in Grafana OnCall

Schedules allow you to map out recurring on-call coverage and automate the escalation of alert notifications to
currently on-call users. With Grafana OnCall, you can customize rotations with a live schedule preview to visualize
your schedule, add users, reorder users, and reference teammates' time zones.

To learn more, see [On-call schedules]({{< relref "../../../calendar-schedules" >}}) which provides the fundamental
concepts for this task.

>**Note:** User working hours are currently hardcoded and cannot be changed. Profile settings to configure this and other options will be added in a future release.

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

Oncall supports multiple **layer** for rotation which allows for overlapping schedule. Layer defines the schedule priority, for example *Layer 2* rotation override *Layer 1* rotation. In this case, users under *Layer 1* would not receive notification during the overlapping time with users under *Layer 2*

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
