---
title: iCal on-call schedules
canonical: https://grafana.com/docs/oncall/latest/on-call-schedules/ical-schedules/
description: "Learn how to manage on-call schedules with iCal import"
keywords:
  - Grafana
  - oncall
  - on-call
  - calendar
title: Import on-call schedules
weight: 300
---

# Import on-call schedules

Use your existing calendar app with iCal format to manage and customize on-call schedules — import rotations and shifts
from your calendar app to Grafana OnCall for widely accessible scheduling. iCal imported schedules appear in Grafana
OnCall as read-only schedules but can be leveraged similarly to a web-based schedule.

> Unfortunately there is a known limitation with Google Calendar import and export.
> Google may take up to 24h to import OnCall's calendar (OnCall -> Google) and sometimes our customers report delay in
> exporting (Google Calendar -> OnCall). If actual calendar is critical for you, we suggest checking
> [web-based scheduling]

## Before you begin

- Verify that your calendar app supports iCal format
- Ensure you have the proper permissions in Grafana OnCall

## Configure an on-call schedule from iCal import

There are three key parts to configuring on-call schedules using iCal import:

1. Create a primary on-call calendar and an optional override calendar in your calendar app.
1. Import the calendars into Grafana OnCall and configure additional schedule settings.
1. Link your schedule to corresponding escalation chains for alert notifications to be sent to the proper on-call user.

### Create your on-call schedule calendar

Create a dedicated calendar to map out your on-call coverage using calendar events. Be sure to take advantage of the
features of your calendar app to configure event recurrence, duplicate events, etc.

>**Note:** The exact steps in this section will vary based on your calendar.

To create an on-call schedule calendar:

1. Create a new calendar in your calendar app, then review and adjust default settings as needed.
1. In your new calendar, create events that represent on-call shifts. You must use Grafana usernames as the event title
to associate users with each shift.
1. Once your on-call calendar is complete, go to your calendar settings to locate the secret iCal URL. For example, in
a Google calendar, this URL can be found in **Settings** > **Settings for my calendars** > **Integrate calendar** >
**Secret address in iCal format**.

To learn more about how to configure your calendar events, refer to Calendar events.

### Import calendar to Grafana On-Call

Once you’ve configured on-call schedules in your calendar app, you can import them via iCal URL to your Grafana OnCall
instance.

>**Note:** Use the secret iCal URL to avoid making the calendar public. If you use the public iCal URL, the calendar
> and event details must be public for Grafana OnCall to read your calendar.

To import an on-call schedule:

1. In Grafana OnCall, navigate to the **Schedules** tab and click **+ New schedule**.
1. Navigate to **Import schedule from iCal URL** and click **+ Create**.
1. Copy the secret iCal URL from your calendar and paste it the **Primary schedule iCal URL** field. Repeat this step
for the **Override schedule iCal URL** field if you have an override calendar.
1. Provide a name and review available schedule settings.
1. When you’re done, click **Create Schedule**.

### Create an override calendar (Optional)

An override calendar allows for on-call flexibility without modifying the primary schedule. You can use an override
calendar to enable users to schedule on-call shifts that will override the primary schedule. Events scheduled on the
override calendar will always override overlapping events on the primary calendar.

1. Create a new calendar using the same calendar service you used to create the primary calendar.
1. Be sure to set permissions that allow team members to edit the calendar.
1. In the **Schedules** tab of Grafana OnCall, select the primary calendar you want to override. Click **Edit**.
1. Enter the secret iCal URL in the **Overrides schedule iCal URL** field and click **Update**.

## Calendar events

Whether your schedule is basic or complex, consider how your on-call coverage is structured before configuring your
calendar events. To minimize the number of calendar events you need to create, try leveraging recurrence settings and
event duplication.

> **Note:** Each calendar event represents one on-call shift for a specific user. For Grafana OnCall to associate a
> calendar event with the intended on-call user, you must use their Grafana username as the event title.  

### Create overlapping schedules (optional)

If you create schedules that overlap, you can prioritize a schedule by adding a level marker to the calendar event
title. You can prioritize schedule overlaps using [L0] - [L9] prioritization. Overlapping calendar events that do not
contain a level marker result in all overlapping users receiving notifications.

For example, users AliceGrafana and BobGrafana have overlapping schedules but BobGrafana is the intended primary
contact. The calendar events titles would be `[L1] BobGrafana` and `[L0] AliceGrafana` - In this case AliceGrafana
maintains the default [L0] status, and would not receive notifications during the overlapping time with BobGrafana.

<!-- markdownlint-disable MD033 -->
{{% docs/reference %}}
[web-schedule]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/on-call-schedules/web-schedule"
[web-schedule]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/on-call-schedules/web-schedule"
{{% /docs/reference %}}
<!-- markdownlint-enable MD033 -->
