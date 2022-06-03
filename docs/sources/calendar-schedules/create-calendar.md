+++
title = "Create an on-call schedule calendar"
description = ""
keywords = ["Grafana", "oncall", "on-call", "calendar"]
aliases = []
weight = 300
+++

# Create an on-call schedule calendar

Create a primary calendar and an optional override calendar to schedule on-call shifts for team members. 

1. In the **Scheduling** section of Grafana OnCall, click **+ Create schedule**.

1. Give the schedule a name. 

1. Create a new calendar in your calendar service and locate the secret iCal URL. For example, in a Google calendar, this URL can be found in **Settings > Settings for my calendars > Integrate calendar**.

1. Copy the secret iCal URL. In OnCall, paste it into the **Primary schedule for iCal URL** field. 
    The permissions you set when you create the calendar determine who can modify the calendar. 

1. Click **Create Schedule**.

1. Schedule on-call times for team members.

    Use the Grafana username of team members as the event name to schedule their on-call times. You can take advantage of all of the features of your calendar service. 

1. Create overlapping schedules (optional). 

    When you create schedules that overlap, you can prioritize a schedule by adding a level marker. For example, if users AliceGrafana and BobGrafana have overlapping schedules, but BobGrafana is the primary contact, you would name his event `[L1] BobGrafana`, AliceGrafana maintains the default `[L0]` status, and would not receive notifications during the overlapping time. You can prioritize up to and including a level 9 prioritization, or `[L9]`.

# Create an override calendar (optional)

You can use an override calendar to allow team members to schedule on-call duties that will override the primary schedule. An override option allows flexibility without modifying the primary schedule. Events scheduled on the override calendar will always override overlapping events on the primary calendar.

1. Create a new calendar using the same calendar service you used to create the primary calendar.

    Be sure to set permissions that allow team members to edit the calendar. 

1. In the scheduling section of Grafana OnCall, select the primary calendar you want to override. 

1. Click **Edit**. 

1. Enter the secret iCal URL in the **Overrides schedule iCal URL** field and click **Update**.