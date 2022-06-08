+++
title = "Connect Slack to Grafana OnCall"
keywords = ["Grafana Cloud", "Alerts", "Notifications", "on-call", "amixr", "oncall", "slack"]
weight = 100
+++

# Connect Slack to Grafana OnCall
Grafana OnCall integrates closely with your Slack workspace to deliver alert group notifications to individuals, groups, and team members. 

## Connect to Slack

Connect your organization's Slack workspace to your Grafana OnCall instance.

>**NOTE:** Only Grafana users with the administrator role can configure OnCall settings.

1. In OnCall, click on the **ChatOps** tab and select Slack in the side menu.
1. Click **Install Slack integration**. 
1. Read the notice and click the button to proceed to the Slack website.
1. Sign in to your organization's workspace.
1. Click **Allow** to allow OnCall to access Slack.
1. Ensure users verify their Slack accounts in their user profile in OnCall.

## Configure Slack in OnCall

In the Slack settings for Grafana OnCall, administrators can set a default Slack channel for notifications and opt to set reminders for acknowledged alerts that can timeout and revert an alert group to the unacknowledged state. 

1. In OnCall, click on the **ChatOps** tab and select Slack in the side menu.
1. In the first dropdown menu, select a default Slack channel.
    When you set up escalation policies to notify Slack channels of incoming alerts, the default will be the one you set here. You will still have the option to select from all the channels available in your organization.
1. In **Additional settings** you can choose how to remind users of acknowledged but unresolved alert groups. You can also select whether and or when to automatically revoke the "acknowledged" status from an alert group to an unacknowledged state.

## Slack settings for on-call calendar scheduling notifications
Admins can configure settings in Slack to notify people and groups about on-call schedules. When an on-call shift notification is sent to a person or channel, click the gear button to access **Notification preferences**. Use the options to configure the behavior of future shift notifications. 