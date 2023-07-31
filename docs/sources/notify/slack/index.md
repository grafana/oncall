---
aliases:
  - ../../chat-options/configure-slack/
canonical: https://grafana.com/docs/oncall/latest/integrations/chatops-integrations/configure-slack/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - amixr
  - oncall
  - slack
title: Slack
weight: 100
---

# Slack integration for Grafana OnCall

The Slack integration for Grafana OnCall incorporates your Slack workspace directly into your incident response workflow
to help your team focus on alert resolution with less friction.

Integrating your Slack workspace with Grafana OnCall allows users and teams to be notified of alerts directly in Slack
with automated alert escalation steps and user notification preferences. There are a number of alert actions that users
can take directly from Slack, including acknowledge, resolve, add resolution notes, and more.

## Before you begin

To install the Slack integration, you must have Admin permissions in your Grafana instance as well as the Slack workspace
that you’d like to integrate with.

For Open Source Grafana OnCall Slack installation guidance, refer to
[Open Source Grafana OnCall][open-source].

## Install Slack integration for Grafana OnCall

1. Navigate to **Settings** tab in Grafana OnCall.
1. From the **Chat Ops** tab, select **Slack** in the side menu.
1. Click **Install Slack integration**.
1. Read the notice and agree to proceed to the Slack website.
1. Provide your Slack workspace URL and sign with your Slack credentials.
1. Click **Allow** to give Grafana OnCall permission to access your Slack workspace.

## Why does OnCall Slack App require so many permissions?
OnCall has an advanced Slack App with dozens of features making it even possible for users to be on-call and work with 
alerts completely inside Slack. The drawback is that our Slack bot requires a lot of permissions and
some of those permissions may sound suspicious, so we commented on them to give you more context.
#### Content and info about you
The bot is using those permissions to receive Slack handles and avatars. 
Those permissions are supporting account matching between Grafana and Slack. 
- **View information about your identity**
- **View profile details about people in your workspace**
#### Content and info about channels & conversations
- **View basic information about public channels in your workspace** 
— this permission is supporting channel selectors in the integration settings so the user could choose where to 
send Alert Groups.
- **View messages and other content in public channels, private channels, direct messages, and group direct messages 
that Grafana OnCall has been added to** — this permission is supporting a feature of adding messages to the resolution 
notes in the Alert Group's Slack thread.
- **View basic information about private channels that Grafana OnCall has been added to** — this permission allows to 
add a slack bot to the private channel and make it selectable in the list of channels. 
So users will be able to route Alert Groups to the private channels.
- **View basic information about direct messages that Grafana OnCall has been added to**
#### Content and info about your workspace
This set of permissions is supporting the ability of Grafana OnCall to match users with Grafana users.
- **View people in your workspace**
- **View email addresses of people in your workspace**
- **View the name, email domain, and icon for workspaces Grafana OnCall is connected to**
- **View user groups in your workspace**
- **View profile details about people in your workspace**
#### Perform actions as you
- **Send messages on your behalf** — this permission may sound suspicious, but it's actually a general ability 
to send messages as the bot: https://api.slack.com/scopes/chat:write Grafana OnCall will not impersonate or post 
using your handle to slack. It will always post as the bot.
#### Perform actions in channels & conversations
- **View messages that directly mention @grafana_oncall in conversations that the app is in**
- **Join public channels in your workspace**
- **Send messages as @grafana_oncall**
- **Send messages as @grafana_oncall with a customized username and avatar**
- **Send messages to channels @grafana_oncall isn't a member of** — users configure channels to publish 
Alert Groups in the OnCall's UI, but the bot is usually not a member of those channels.
- **Upload, edit, and delete files as Grafana OnCall** — the bot is using this permission: 
https://api.slack.com/scopes/files:write to be able to send files to the channel. 
The bot will not delete or read files sent by other users.
- **Start direct messages with people**
- **Add and edit emoji reactions**
#### Perform actions in your workspace
- **Add shortcuts and/or slash commands that people can use** — the permission is used to add /escalate and /oncall 
(deprecated) slack commands.
- **Create and manage user groups** — the permission is used to automatically update user groups linked to on-call
schedules. It will add users once their on-call shift starts and remove them once the on-call shift ends.
- **Set presence for Grafana OnCall** 

## Post-install configuration for Slack integration

Configure the following additional settings to ensure Grafana OnCall alerts are routed to the intended Slack channels
and users:

1. From your **Slack integration** settings, select a default slack channel in the first dropdown menu. This is where
   alerts will be sent unless otherwise specified in escalation chains.
2. In **Additional Settings**, configure alert reminders for alerts to retrigger after being acknowledged for some
   amount of time.
3. Ensure all users verify their slack account in their Grafana OnCall **users info**.

### Connect Slack user to Grafana OnCall

1. From the **Users** tab in Grafana OnCall, click **View my profile**.
1. In the **User Info** tab, navigate to **Slack username**, click **Connect**.
1. Follow the instructions to verify your account.

### Configure Escalation Chains with Slack notifications

Once your Slack integration is configured you can configure Escalation Chains to notify via Slack messages for alerts
in Grafana OnCall.

There are two Slack notification options that you can configure into escalation chains, notify whole Slack channel and
notify Slack user group:

1. In Grafana OnCall, navigate to the **Escalation Chains** tab then select an existing escalation chain or
   click **+ New escalation chain**.
2. Click the dropdown for **Add escalation step**.
3. Configure your escalation chain with automated Slack notifications.

### Configure user notifications with Slack mentions

To be notified of alerts in Grafana OnCall via Slack mentions:

1. Navigate to the **Users** tab in Grafana OnCall, click **Edit** next to a user.
2. In the **User Info** tab, edit or configure notification steps by clicking + Add Notification step
3. select **Notify by** in the first dropdown and select **Slack mentions** in the second dropdown to receive alert
   notifications via Slack mentions.

### Configure on-call notifications in Slack

The Slack integration for Grafana Oncall supports automated Slack on-call notifications that notify individuals and
teams of their on-call shifts. Admins can configure shift notification behavior in Notification preferences:

1. When an on-call shift notification is sent to a person or channel, click the gear icon to
   access **Notifications preferences**.
2. Configure on-call notifications for future shift notifications.

## Slack commands and message shortcuts

The Grafana OnCall Slack app includes helpful message shortcuts and slash commands.

### Slack `/escalate` command

Use `/escalate` to page a team (and additional responders) directly from Slack.

1. Type `/escalate` in the message box of any Slack channel then click **Send**.
1. Fill out the **Create Alert Group** form then click **Submit**.
1. Once the Grafana OnCall app sends a Slack message with the newly created alert, the alert group is open and firing.

It's also possible to page additional responders for an existing alert group. To do so, use the "Responders" button
in the alert group message. [Learn more about paging people manually.][integrations-manual]

### Slack `/oncall` command

> **DEPRECATED: `/oncall` is deprecated and WILL BE REMOVED in a future release. Use `/escalate` instead.**

Use the `/oncall` Slack command to create a new alert group directly from Slack targetting a team and/or route.

1. Type `/oncall` in the message box of the desired Slack channel then click **Send**.
1. Fill out the **Start New Escalation** creation form then click **Submit**.
1. Once the Grafana OnCall app sends a Slack message with the newly created alert, the alert group is open and firing.

### Message shortcuts

Use message shortcuts to add resolution notes directly from Slack. Message shortcuts are available in the More actions menu from any message.

> **Note:** In order to associate the resolution note to an alert group, this message shortcut can only be applied to messages in the thread of an alert group.

1. From an alert group thread, navigate to the Slack message that you wish to add as a resolution note.
1. Hover over the message and select **More actions** from the menu options.
1. Select **Add as resolution note**.
1. The Grafana OnCall app will react to the message in Slack with the memo emoji and add the message to the alert group timeline.

{{% docs/reference %}}
[open-source]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/open-source"
[open-source]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/open-source"

[integrations-manual]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/integrations/manual"
[integrations-manual]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/integrations/manual"
{{% /docs/reference %}}
