---
title: Zoom Team Chat
menuTitle: Zoom Team Chat
description: How to connect Zoom Team Chat for alert group notifications.
weight: 950
keywords:
  - OnCall
  - Notifications
  - ChatOps
  - Zoom
  - Team Chat
canonical: https://grafana.com/docs/oncall/latest/manage/notify/zoom/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/manage/notify/zoom/
  - /docs/grafana-cloud/alerting-and-irm/oncall/notify/zoom/
---

# Zoom Team Chat integration for Grafana OnCall

The Zoom Team Chat integration for Grafana OnCall allows connecting a Zoom Team Chat channel directly
into your incident response workflow to help your team focus on alert resolution with less friction.

## Features

- Receive alert notifications in Zoom Team Chat channels
- Interactive message cards with action buttons (Acknowledge, Resolve, Silence)
- Color-coded alert status indicators
- User mentions for actions taken
- Customizable message footer with branding

## Before you begin

To install the Zoom Team Chat integration, you must have:

- Admin permissions in your Grafana OnCall setup
- A Zoom Team Chat App configured in the [Zoom App Marketplace](https://marketplace.zoom.us/)
- The required environment variables configured in your OnCall deployment

For detailed setup instructions, see the [Zoom Team Chat integration reference]({{< relref "../../configure/integrations/references/zoom" >}}).

## Connect to a Zoom Team Chat Channel

1. In Grafana OnCall, navigate to **Settings** > **ChatOps** > **Zoom**
2. Click **Connect Zoom Channel**
3. Enter the Zoom channel JID or select from available channels
4. Click **Create** to add the channel
5. Set a default channel for alerts

## Configure user notifications

Users can receive personal alert notifications via Zoom:

1. Go to **Users** and click **Edit** on your profile
2. In the notification preferences section, click **+ Add Notification step**
3. Select **Zoom** as the notification method
4. Connect your Zoom account if prompted

## Using Zoom notifications in Escalation Chains

To send alert notifications to a Zoom channel:

1. Navigate to **Escalation Chains**
2. Create or edit an escalation chain
3. Add a step and select **Notify Zoom channel**
4. Choose the Zoom channel from the dropdown

## Alert actions in Zoom

When an alert is sent to Zoom, users can interact with it using the following buttons:

| Action | Description |
|--------|-------------|
| ✅ Acknowledge | Mark the alert as acknowledged |
| ✔️ Resolve | Mark the alert as resolved |
| 🔇 Silence | Silence the alert for a specified duration |
| ↩️ Unacknowledge | Revert acknowledgment |
| ↩️ Unresolve | Revert resolution |
| 🔔 Unsilence | Remove silence from the alert |

### Silence options

The Silence button provides multiple duration options:
- 30 minutes
- 1 hour
- 2 hours
- 4 hours
- 6 hours
- 12 hours
- 24 hours
- Forever

## Alert status indicators

Alert messages display color-coded status indicators:

| Status | Color | Indicator |
|--------|-------|-----------|
| Firing | Red | 🔴 |
| Acknowledged | Gray | ⚪ |
| Resolved | Green | ✅ |
| Silenced | Purple | 🔇 |

## Troubleshooting

### Alerts not appearing in Zoom

1. Verify the Zoom integration is enabled (`FEATURE_ZOOM_INTEGRATION_ENABLED=True`)
2. Check that the Zoom bot has been added to the target channel
3. Verify the channel is correctly configured in OnCall
4. Check OnCall logs for error messages

### Action buttons not responding

1. Verify the webhook endpoint is correctly configured in your Zoom app
2. Check that the webhook secret token matches
3. Ensure the Zoom app has the required scopes

### User mentions not working

1. Ensure users have connected their Zoom accounts in OnCall
2. Verify the Zoom bot has permission to read user information
