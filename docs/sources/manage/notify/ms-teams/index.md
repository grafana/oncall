---
title: MS Teams integration for Grafana OnCall
menuTitle: Microsoft Teams
description: Learn more about the Microsoft Teams integration for Grafana OnCall.
weight: 500
keywords:
  - OnCall
  - Notifications
  - ChatOps
  - MS Teams
  - Microsoft
  - Channels
labels:
  products:
    - cloud
canonical: https://grafana.com/docs/oncall/latest/manage/notify/ms-teams/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/manage/notify/ms-teams/
  - /docs/grafana-cloud/alerting-and-irm/oncall/notify/ms-teams
  - ../../chat-options/configure-teams/ # /docs/oncall/<ONCALL_VERSION>/chat-options/configure-teams/
  - ../../notify/ms-teams/ # /docs/oncall/<ONCALL_VERSION>/notify/ms-teams/
---

# MS Teams integration for Grafana OnCall

{{< admonition type="note" >}}
This integration is available exclusively on Grafana Cloud.
{{< /admonition >}}

The Microsoft Teams integration for Grafana OnCall embeds your MS Teams channels directly into your incident response
workflow to help your team focus on alert resolution.

Integrating MS Teams with Grafana OnCall allows users to be notified of alerts directly in MS Teams with automated escalation
steps and user notification preferences. Users can also take action on alerts directly from MS Teams, including
acknowledge, unacknowledge, resolve, and silence.

## Before you begin

The following is required to connect to Microsoft Teams to Grafana OnCall:

- You must have Admin permissions in your Grafana Cloud instance.
- You must have Owner permissions in Microsoft Teams.
- Install the Grafana IRM app from the [Microsoft Marketplace](https://appsource.microsoft.com/en-us/product/office/WA200004307).

## Connect Microsoft Teams with Grafana OnCall

{{< admonition type="note" >}}
A Microsoft Teams workspace can only be connected to one Grafana Cloud instance and cannot be connected to multiple environments.
{{< /admonition >}}

To connect Microsoft Teams with Grafana OnCall:

1. In Grafana OnCall, open **Settings** and click **Chat Ops**.
1. From the **Chat Ops** tab, select **Microsoft Teams** in the side menu.
1. Follow the in-app instructions to add the Grafana IRM app to your Teams workspace.
1. After your workspace is connected, copy and paste the provided code into a Teams channel to add the IRM bot, then click **Done**.
1. To add additional channels click **+Add MS Teams channel** and repeat step 3 as needed.

## Post-install configuration for Microsoft Teams integration

Configure the following settings to ensure Grafana OnCall alerts are routed to the intended Teams channels and users:

- Set a default channel from the list of connected MS Teams channels.
This is where alerts will be sent unless otherwise specified in escalation chains.
- Ensure all users verify their MS Teams account in their Grafana OnCall user profile.

### Connect Microsoft Teams user to Grafana OnCall

1. From the **Users** tab of Grafana OnCall, click **View my profile**.
1. In the **User Info** tab, locate **Notification channels**, **MS Teams**, and click **Connect account**.
1. Follow the steps provided to connect your Teams user.
1. Navigate back to your Grafana OnCall profile and verify that your Microsoft Teams account is linked to your Grafana
   OnCall user.

### Configure user notifications with Microsoft Teams

To be notified of Grafana OnCall alerts via MS Teams:

1. Navigate to the **Users** tab in Grafana OnCall, click **Edit** next to a user.
1. In the **User Info** tab, edit or configure notification steps by clicking **+Add Notification step**
1. Select **Notify by** in the first dropdown and select **Microsoft Teams** in the second dropdown to receive alert
   notifications in Teams.

### Configure escalation chains to post to Microsoft Teams channels

Once your MS Teams integration is configured you can add an escalation step at the integration level to automatically
send alerts from a specific integration to a channel in MS Teams.

To automatically send alerts from an integration to MS Teams channels:

1. Navigate to the **Integrations** tab in Grafana OnCall, select an existing integration or
   click **+New integration to receive alerts**.
1. From the integrations settings, navigate to the escalation chain panel.
1. Enable **Post to Microsoft Teams channel** by selecting a channel to connect from the dropdown.
