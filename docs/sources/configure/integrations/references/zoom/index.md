---
title: Zoom Team Chat integration for Grafana OnCall
menuTitle: Zoom Team Chat
description: Learn more about Zoom Team Chat integration for Grafana OnCall.
weight: 0
keywords:
  - OnCall
  - Notifications
  - ChatOps
  - Zoom
  - Team Chat
  - Integration
  - Channels
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/references/zoom/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/zoom/
---

# Zoom Team Chat integration for Grafana OnCall

The Grafana OnCall Zoom Team Chat integration allows you to receive alert notifications directly in your Zoom Team Chat channels,
helping your team respond to incidents quickly without leaving Zoom.

## Key features and benefits

Integrating your Zoom Team Chat allows users and teams to be notified of alerts directly in Zoom channels with interactive message cards.
Users can take alert actions directly from Zoom, including:

- **Acknowledge** - Acknowledge an alert to indicate you're working on it
- **Resolve** - Mark an alert as resolved
- **Silence** - Silence an alert for a specified duration (30 minutes, 1 hour, 2 hours, etc.)
- **Unacknowledge/Unresolve/Unsilence** - Revert previous actions

Alert messages include:
- Alert status with color-coded indicators (Red for Firing, Gray for Acknowledged, Green for Resolved, Purple for Silenced)
- Alert details and context
- Interactive action buttons
- Custom footer branding

## Before you begin

To set up the Zoom Team Chat integration, you'll need:

- Admin role in Grafana OnCall
- A Zoom General App (either Admin-managed or User-managed)
- Zoom marketplace admin access to create and configure the app

## Create a Zoom Team Chat App

1. Go to the [Zoom App Marketplace](https://marketplace.zoom.us/) and sign in
2. Click **Develop** > **Build App**
3. Select **General Apps** and click **Create**

### Basic Information

1. **Select how the app is managed**:
   - **Admin-managed**: Account admins can add and manage this app. It can access and manage users' data depending on the scope selection.
   - **User-managed**: Individual users can add and manage this app. The app only has access to authorized users' data.

2. **App Credentials** - Note the following values:
   - **Client ID**
   - **Client Secret**

3. **OAuth Information**:
   - Set **OAuth Redirect URL** to: `https://your-oncall-domain/api/internal/v1/complete/zoom-login/`
   - Add the same URL to **OAuth Allow Lists**

### Access

1. **Token**:
   - Note the **Secret Token** - This is used to verify event notifications sent by Zoom

2. **General Features**:
   - Enable **Event Subscription** if you need webhook notifications

### Surface

1. **Select where to use your app**:
   - Check **Team Chat** to enable Team Chat integration

2. **In-client App Features**:
   - Enable **In-Client OAuth** - Users can complete the authorization in Zoom Client without opening system browser

### Team Chat Subscription

1. Enable **Team Chat Subscription** feature
2. Set **Bot Endpoint URL** to: `https://your-oncall-domain/api/internal/v1/webhooks/zoom/`
3. The following scope is automatically selected: `imchat:bot`

### Required Scopes

Ensure your app has the following scopes (add via **Scopes** > **+ Add Scopes**):

**Team Chat:**

| Scope | Description |
|-------|-------------|
| `team_chat:write:user_message` | Create a chat message for a user |
| `team_chat:write:reminder` | Create a reminder for a message |
| `app:channel_content:write` | Enable Chatbot within Zoom Team Chat Channel |
| `imchat:userapp` | Enable user managed app within Zoom Team Chat client |
| `team_chat:read:file` | Get chat file information |
| `team_chat:read:channel` | View a chat channel |
| `team_chat:read:list_members` | View a chat channel's members |

**User:**

| Scope | Description |
|-------|-------------|
| `user:read:user` | View a user |

## Configure Zoom integration in Grafana OnCall

### Environment Variables

Set the following environment variables in your OnCall deployment:

| Variable | Description |
|----------|-------------|
| `FEATURE_ZOOM_INTEGRATION_ENABLED` | Set to `True` to enable the integration |
| `ZOOM_CLIENT_ID` | Your Zoom app Client ID |
| `ZOOM_CLIENT_SECRET` | Your Zoom app Client Secret |
| `ZOOM_ACCOUNT_ID` | Your Zoom Account ID (Server-to-Server OAuth only) |
| `ZOOM_BOT_JID` | Your Zoom bot JID |
| `ZOOM_WEBHOOK_SECRET_TOKEN` | Your Zoom webhook secret token |
| `ZOOM_LOGIN_RETURN_REDIRECT_HOST` | OnCall external URL for OAuth redirect |
| `ZOOM_MESSAGE_FOOTER` | (Optional) Custom footer text for messages |
| `ZOOM_MESSAGE_FOOTER_ICON` | (Optional) Custom footer icon URL |

### Helm Chart Configuration

If using Helm, configure the Zoom integration in your values.yaml:

```yaml
oncall:
  zoom:
    enabled: true
    clientId: "your-client-id"
    clientSecret: "your-client-secret"
    accountId: "your-account-id"  # Optional, for Server-to-Server OAuth
    botJid: "your-bot-jid"
    webhookSecretToken: "your-webhook-secret"
    redirectHost: "https://oncall.example.com"
    messageFooter: "Your Company Alert System"
    messageFooterIcon: "https://your-logo-url"
```

## Connect a Zoom channel to OnCall

1. In OnCall, navigate to **Settings** > **ChatOps** > **Zoom**
2. Click **Connect Zoom Channel**
3. Select the Zoom Team Chat channel where you want to receive alerts
4. Configure the default channel for your organization

## Configure escalation chains with Zoom notifications

After setting up your Zoom integration, you can configure escalation chains to send notifications to Zoom:

1. Navigate to **Escalation Chains** in OnCall
2. Create or edit an escalation chain
3. Add a step to **Notify Zoom channel**
4. Select the configured Zoom channel

## Configure user notification preferences

Users can receive personal notifications via Zoom:

1. Go to **Users** and edit your profile
2. Under notification preferences, add **Zoom** as a notification method
3. Connect your Zoom account if prompted

## Alert message format

Zoom alert messages include:

- **Header**: Alert title with status indicator
- **Status**: Current alert status (Firing, Acknowledged, Resolved, Silenced)
- **Alert Details**: Key information from the alert
- **Action Buttons**: Interactive buttons for quick actions
- **Footer**: Timestamp and optional custom branding

### Status Colors

| Status | Color |
|--------|-------|
| Firing | Red (#E53935) |
| Acknowledged | Gray (#757575) |
| Resolved | Green (#43A047) |
| Silenced | Purple (#9400D3) |

## Troubleshooting

### Messages not appearing in Zoom

1. Verify the Zoom app is properly installed and activated
2. Check that the bot has been added to the target channel
3. Verify webhook URL is correctly configured
4. Check OnCall logs for any error messages

### Interactive buttons not working

1. Ensure the interactive message endpoint is correctly configured
2. Verify the webhook secret token matches
3. Check that required scopes are granted to the app

### Authentication errors

1. Verify Client ID and Client Secret are correct
2. For Server-to-Server OAuth, ensure Account ID is set
3. Check that the app has not been deactivated
