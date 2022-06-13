---
aliases:
  - /docs/grafana-cloud/oncall/getting-started/
  - /docs/oncall/latest/getting-started/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
title: Getting started with Grafana OnCall
weight: 100
---

# Getting started with Grafana OnCall

These procedures introduce you to the configuration of user settings, how to set up escalation policies, and how to use your calendar service for on-call scheduling.

## Before you begin

You must have a [Grafana Cloud](https://grafana.com/products/cloud/) account or [Open Source Grafana OnCall]({{< relref " open-source.md" >}})

Each supported integration and the associated monitoring system has a slightly different configuration method. These methods will not be explained in this guide, however, you can follow the online instructions provided when adding an integration.

## Configure user notification policies

You can configure how each user will receive notifications when they are assigned in escalation policies.

1. Find users.

   Select the **Users** tab and use the browser to search for a user in your organization.

1. Configure user settings.

   Add and verify a phone number and a Slack username if you want to deliver notifications using these mediums.
   <br>

   > **NOTE:** To edit a user's username, email, or role, you must do so in the **Users** tab in the **Configuration** menu of your Grafana instance.

1. Configure notification settings.

   You can configure the notification medium and frequency for each user. **Important Notifications** are specified in escalation steps.

## Connect to integration data sources

You use Grafana OnCall to connect to the monitoring services of your alert sources listed in the Grafana OnCall **Integrations** section.

1. Connect to a alert source with configured alerts.

   In Grafana OnCall, click on the **Integrations** tab and click **+ New integration for receiving alerts**.

1. Select an integration from the provided options.

   If you want to use an integration that is not listed, you must use webhooks.

1. Configure your integration.

   Each integration has a different method of connecting to Grafana OnCall. For example, if you want to connect to your Grafana alert source, select Grafana and follow the instructions.

## Configure escalation policies

You can use **escalation chains** to determine ordered escalation procedures. Configuring escalation chains allows you to set up a chain of incident notification actions that trigger if certain conditions that you specify are not met.

1. Click on the integration tile for which you want to define escalation policies.

   The **Escalations** section for the notification is in the pane to the right of the list of notifications.
   You can click **Change alert template and grouping** to customize the look of the alert. You can also do this by clicking the **Settings** (gear) icon in the integration tile.

1. Create an escalation chain.

   In the escalation pane, click the **escalate to** menu to choose from previously added escalation chains, or create a new one by clicking **Create a new**. This will be the name of the escalation policy you define.

1. Add escalation steps.

   Click **Add escalation step** to choose from a set of actions and specify their triggering conditions. By default, the first step is to notify a slack channel or user. Specify users or channels or toggle the switch to turn this step off.

   To mark an escalation as **Important**, select the option from the step **Start** dropdown menu. User notification policies can be separately defined for **Important** and **Default** escalations.

1. Add a route.

   To add a route, click **Add Route**.

   You can set up a single route and specify notification escalation steps, or you can add multiple routes, each with its own configuration.

   Each route added to an escalation policy follows an `IF`, `ELSE IF`, and `ELSE` path and depends on the type of alert you specify using a regular expression that matches content in the payload body of the alert. You can also specify where to send the notification for each route.

   For example, you can send notifications for alert incidents with `\"severity\": \"critical\"` in the payload to an escalation chain called `Bob_OnCall`. You can create a different route for alerts with the payload `\"namespace\" *: *\"synthetic-monitoring-dev-.*\"` and select a escalation chain called `NotifySecurity`.

   You can set up escalation steps for each route in a chain.

   > **NOTE:** When you modify an escalation chain or a route, it will modify that escalation chain across all integrations that use it.

## Use calendars to configure on-call schedules

You can use any calendar with an iCal address to schedule on-call times for users. During these times, notifications configured in escalation chains with the **Notify users from an on-call schedule** setting will be sent to the the person scheduled. You can also schedule multiple users for overlapping times, and assign prioritization labels for the user that you would like to notify.

1. In the **Scheduling** section of Grafana OnCall, click **+ Create schedule**.

1. Give the schedule a name.

1. Create a new calendar in your calendar service and locate the secret iCal URL. For example, in a Google calendar, this URL can be found in **Settings > Settings for my calendars > Integrate calendar**.

1. Copy the secret iCal URL. In OnCall, paste it into the **Primary schedule for iCal URL** field.
   The permissions you set for the calendar determine who can modify the calendar.

1. Click **Create Schedule**.

1. Schedule on-call times for team members.

   Use the usersname of team members as the event name to schedule their on-call times. You can take advantage of all of the features of your calendar service.

1. (Optional) Create overlapping schedules.

   When you create schedules that overlap, you can prioritize a schedule by adding a level marker. For example, if users AliceGrafana and BobGrafana have overlapping schedules, but BobGrafana is the primary contact, you would name his event `[L1] BobGrafana`, AliceGrafana maintains the default `[L0]` status, and would not receive notifications during the overlapping time. You can prioritize up to and including level 9, or `[L9]`.

### (Optional) Create an override calendar.

You can use an override calendar to allow team members to schedule on-call duties that will override the primary schedule. An override option allows flexibility without modifying the primary schedule. Events scheduled on the override calendar will always override overlapping events on the primary calendar.

1. Create a new calendar using the same calendar service you used to create the primary calendar.

   Be sure to set permissions that allow team members to edit the calendar.

1. In the scheduling section of Grafana OnCall, select the primary calendar you want to override.

1. Click **Edit**.

1. Enter the secret iCal URL in the **Overrides schedule iCal URL** field and click **Update**.
