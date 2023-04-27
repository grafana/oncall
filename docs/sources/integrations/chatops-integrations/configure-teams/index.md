---
aliases:
  - ../../chat-options/configure-teams/
  - /docs/oncall/latest/integrations/chatops-integrations/configure-teams/
canonical: https://grafana.com/docs/oncall/latest/integrations/chatops-integrations/configure-teams/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - amixr
  - oncall
  - MS Team
  - Microsoft
title: Microsoft Teams integration for Grafana OnCall
weight: 500
---

# Microsoft Teams integration for Grafana OnCall

The Microsoft Teams integration for Grafana OnCall embeds your MS Teams channels directly into your incident response
workflow to help your team focus on alert resolution.

Integrating MS Teams with Grafana OnCall allows users to be notified of alerts directly in MS Teams with automated escalation
steps and user notification preferences. Users can also take action on alerts directly from MS Teams, including
acknowledge, unacknowledge, resolve, and silence.

## Before you begin

> NOTE: **This integration is available to Grafana Cloud instances of Grafana OnCall only.**

The following is required to connect to Microsoft Teams to Grafana OnCall:

- You must have Admin permissions in your Grafana Cloud instance.
- You must have Owner permissions in Microsoft Teams.
- Install the Grafana OnCall app from the [Microsoft Marketplace](https://appsource.microsoft.com/en-us/product/office/WA200004307).

## Install Microsoft Teams integration for Grafana OnCall

1. Navigate to **Settings** tab in Grafana OnCall.
1. From the **ChatOps** tab, select **Microsoft Teams** in the side menu.
1. Follow the steps provided to connect to your Teams channels, then click **Done**.
1. To add additional teams and channels click **+Add MS Teams channel** again and repeat step 3 as needed.

## Post-install configuration for Microsoft Teams integration

Configure the following settings to ensure Grafana OnCall alerts are routed to the intended Teams channels and users:

- Set a default channel from the list of connected MS Teams channels. This is where alerts will be sent unless otherwise
  specified in escalation chains.
- Ensure all users verify their MS Teams account in their Grafana OnCall user profile.

### Connect Microsoft Teams user to Grafana OnCall

1. From the **Users** tab in Grafana OnCall, click **View my profile**.
1. Navigate to **Microsoft Teams username**, click **Connect**.
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
