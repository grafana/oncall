---
title: Slack integration for Grafana IRM
menuTitle: IRM Slack
description: Learn more about Slack integration for Grafana IRM.
weight: 0
_build:
  list: false
keywords:
  - OnCall
  - IRM
  - Notifications
  - ChatOps
  - Slack
  - Integration
  - Channels
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/references/slack/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/slack/
  - ../../references/slack/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/slack
---

# Slack integration for Grafana IRM

The Grafana IRM Slack integration incorporates your incident response workflow directly into your Slack workspace,
helping your team focus on alert resolution with less friction.

{{< admonition type="note" >}}
The OnCall Slack app has been rebranded as the Grafana IRM Slack app, which now has incident management features.
The legacy Incident Slack integration is being deprecated.

If you have an existing installation of the legacy Slack integrations, refer to the [migration instructions](#migrate-to-the-grafana-irm-slack-integration)
for more information on how to migrate to the Grafana IRM Slack integration.
{{< /admonition >}}

## Key features and benefits

Integrating your Slack workspace allows users and teams to be notified of alerts directly in Slack with automated alert escalation steps and user notification preferences.
Users can take a number of alert actions directly from Slack, including acknowledging and resolving alert groups, adding resolution notes, and more.

Refer to the following sections to learn more:

- [Configure Escalation Chains with Slack notifications](#configure-escalation-chains-with-slack-notifications)
- [Configure user notifications policies with Slack mentions](#configure-user-notifications-policies-with-slack-mentions)
- [Configure on-call notifications in Slack](#configure-on-call-notifications-in-slack)

When it comes to incidents, users can declare, collaborate on, and manage incident-worthy events without leaving Slack.
They can also automatically create incident-specific channels, track the timeline of events, interact with incidents via Slash commands, and more.

Refer to the following sections to learn more:

- [Create incident Slack channels](#configure-incident-slack-channels)
- [Configure incident announcements](#configure-incident-announcements)
- [Interact with incidents from Slack via Slash commands](#incident-related-commands)

## Before you begin

To install the Grafana IRM Slack app:

- You must have an Admin role in Grafana IRM
- You must be a Slack workspace admin or owner
- Allow Grafana IRM to access your Slack workspace

Once your IRM account has been added to your Slack workspace, Admins and Editors can configure escalation chains and other notifications to route to designated
Slack channels.

In order to use the Slack slash command `/grafana`, you must be an IRM user with a linked Slack account.
To learn more, refer to [Connect your Slack user to Grafana IRM](#connect-your-slack-user-to-grafana-irm).

## Install Slack integration for Grafana IRM

Currently, the Grafana IRM Slack integration can be installed from Grafana OnCall or Grafana Incident.
Installing the integration in either location will automatically install it for the other.

{{< admonition type="note" >}}
If you already have the OnCall or Incident Slack integration installed, use the instructions in [Migrate to the IRM Slack integration](#migrate-to-the-grafana-irm-slack-integration).
{{< /admonition >}}

Follow these steps to install the Slack integration from Grafana OnCall:

1. Navigate to the **Settings** tab in Grafana OnCall.
1. From the **ChatOps** tab, select **Slack** in the side menu.
1. Click **Install integration**.
1. Once redirected to the Slack connection page, verify the Slack workspace is correct or **Add another workspace**.
1. If needed, provide your Slack workspace URL and sign with your Slack credentials.
1. Follow the Slack prompts to review permissions and specify a default channel.
1. Click **Allow** to give Grafana IRM permission to access your Slack workspace.

Follow these steps to install the Slack integration from Grafana Incident:

1. Navigate to the **Integrations** tab in Grafana Incident.
1. Click the **Slack IRM** tile and then click **Install Integration**.
1. Once redirected to the Slack connection page, verify the Slack workspace is correct or **Add another workspace**.
1. If needed, provide your Slack workspace URL and sign with your Slack credentials.
1. Follow the Slack prompts to review permissions and specify a default channel.
1. Click **Allow** to give Grafana IRM permission to access your Slack workspace.

For more information about the required permissions, refer to the [Permissions](#permissions-scope-and-purpose) section.

## Migrate to the Grafana IRM Slack integration

The Grafana IRM Slack integration combines the features of both OnCall and Incident into a single app.
The OnCall Slack app has been rebranded as the Grafana IRM Slack app and now includes incident management capabilities.

This integration is IRM-wide, meaning that once the Grafana IRM Slack integration is installed or re-installed in OnCall,
it will automatically be available for use in Incident, and vice versa.
The same applies to the uninstall process—uninstalling the IRM app from OnCall will also remove it from Incident.

There are two ways to upgrade to the new integration, depending on your current installation.

### Migrate from the OnCall Slack app to the IRM Slack app

To upgrade from the OnCall Slack integration to the Grafana IRM Slack integration,
you only need to approve the additional permissions required for Incident management functionality.
Migrating to the IRM Slack app will not affect your existing OnCall Slack-related configuration, including channels, users, and schedules.

{{< admonition type="note" >}}
The `/escalate` command is deprecated, please use `/grafana escalate` instead. Refer to [Available Slack commands](#available-slack-commands) for more information.
{{< /admonition >}}

From OnCall, follow these steps to upgrade:

1. Navigate to the **Settings** tab in Grafana OnCall.
2. From the **ChatOps** tab, select **Slack** in the side menu.
3. Click **Migrate**
4. Once redirected to the Slack connection page, verify the Slack workspace and follow the Slack prompts to review permissions and specify a default channel.
5. Click **Allow** to reauthorize Grafana IRM to access your Slack workspace with additional permissions.

Migrating to the Grafana IRM Slack integration requires the following additional permissions:

- `Bookmarks:read`
- `Bookmarks:write`
- `Channels:manage`
- `Groups:write`
- `Pins:read`
- `Reactions:read`
- `Incoming-webhook`

Refer to the [Permissions](#permissions-scope-and-purpose) section for detailed information.

### Migrate from the Incident Slack app to the IRM Slack app

The Grafana Incident Slack integration is now considered legacy,
and you will need to migrate to the new Grafana IRM Slack integration by installing the updated Grafana IRM Slack app.

During this migration, your existing Incident Slack settings, including incident announcements and automatic channel creation, will be preserved.
The new Grafana IRM Slack app will be installed, along with the `/grafana incident` command.
You will still be able to manage incidents that were started before the migration using the legacy app and the `/incident` command.

From Incident, follow these steps to migrate:

1. Navigate to the **Integrations** tab in Grafana OnCall.
2. Click the **Slack IRM** tile and then click **Install Integration**.
3. Once redirected to the Slack connection page, verify the Slack workspace and follow the Slack prompts to review permissions and specify a default channel.
4. Click **Allow** to authorize Grafana IRM to access your Slack workspace.

Refer to the [Permissions](#permissions-scope-and-purpose) section for more information.

## Connect your Slack user to Grafana IRM

For users to gain full access to Grafana IRM functionality in Slack, follow these steps to map your Grafana IRM user account to your Slack user account:

1. In Grafana OnCall, navigate to the **Users** tab and click **View my profile**.
1. Under the **User Info** tab, find the Slack username section and click **Connect**.
1. Follow the prompts to verify and link your Slack account.

## Configure channels and notifications

Grafana IRM provides flexible configuration options to tailor Slack notifications to your team's needs.
This section outlines how to set up escalation chains, user notifications, on-call notifications, and incident channels within Slack.

### Configure Escalation Chains with Slack notifications

After setting up your Slack integration, you can configure escalation chains to send notifications via Slack for alerts in Grafana OnCall.

There are two Slack notification methods that can be integrated into escalation chains:

- Notify all members of a Slack channel
- Notify a specific Slack user group

To configure these in your escalation chains:

1. In Grafana OnCall, navigate to the **Escalation Chains** tab.
1. Select an existing escalation chain or create a new one by clicking **+ New escalation chain**.
1. Use the dropdown under **Add escalation step** to choose and configure your Slack notification preferences.

### Configure user notifications policies with Slack mentions

You can receive alert notifications directly via Slack mentions, ensuring that critical alerts reach you immediately:

1. From the **Users** tab in Grafana OnCall and click **Edit** next to the user you want to configure.
1. In the **User Info** tab, click **+ Add Notification step**.
1. Choose **Notify by** in the first dropdown, then select **Slack mentions** in the second dropdown to receive notifications through Slack mentions.

### Configure on-call notifications in Slack

The IRM Slack integration also supports automated notifications for on-call shifts, helping teams stay informed of their duties.
Admins can set up these notifications in the Notification Preferences section:

1. When an on-call shift notification is sent to a person or channel, click the **gear icon** to open **Notifications preferences**.
1. Configure the notification behavior for future shifts according to your team's preferences.

### Configure Incident Slack channels

Grafana IRM allows you to customize the names of incident-specific Slack channels by setting prefixes, making it easier to organize and search for incident channels.
To customize Slack channel prefixes:

1. Click **Incident** in the left-side menu.
1. Go to **Settings**.
1. Scroll down to the **Prefixes** section in the Settings page.
1. Click **+ Add Prefix** and provide a name and description.
1. Edit any existing prefixes as needed, then click **Update**.
1. Once your prefixes are defined, you can choose which prefix to use when declaring an incident in Grafana Incident.

### Configure Incident announcements

Incident announcements help keep your team aware and informed during critical events.
Configure these announcements to ensure that stakeholders are kept up-to-date in Slack during an incident.

To configure Incident announcements:

1. Navigate to **Incident** in the left-side menu, then click **Integrations**.
1. Click **Slack IRM** to open the Slack IRM integration page.
1. Select the Slack channel where you want to send notifications.
You can either choose from the dropdown menu or manually add your Channel ID. The Channel ID can be found in the Slack channel’s **About** tab.
1. Define the incident-specific fields:

- **Incident type**: Choose whether the incident is internal or private.
- **Include incidents**: Specify which types of incidents to announce—options include all incidents, drills, or non-drills.

1. Apply filters to your incident announcements to tailor the notifications to specific channels:

- **Incident filter**: For example, you might filter by label, such as `label: 'squad:datasources'`.

### Manage Slack attachments

When you use the 🤖 emoji reaction on a Slack message containing a file, the file is securely copied to Grafana Cloud storage.
This ensures your incident timeline remains intact, even if the file is later deleted from Slack. Here’s how it works:

- **File retention**: Control attachment retention in your incident timeline. Removing the 🤖 reaction will delete the attached files from Grafana Cloud storage.
- **Incident web app**: Deleting an item from the timeline within the Incident web app also removes the associated file from Grafana Cloud storage.
- **File size limit**: Files in Grafana Incident are limited to 100MB. Files too large to persist will still be accessible via a link to the source file in Slack.

## Available Slack commands

{{< admonition type="note" >}}
The `/escalate` and `/incident` Slack commands have been deprecated. Use `/grafana` to learn more.
{{< / admonition >}}

The `/grafana` Slack commands allow users and teams to respond to alert groups and collaborate on incidents directly from Slack.

{{< admonition type="tip" >}}
Use the 🤖 robot emoji Slack reaction to add important messages to the incident timeline.
{{< /admonition >}}

| Command              | Description                          |
|----------------------|--------------------------------------|
| `/grafana`           | List of all `/grafana` commands      |
| `/grafana stacks`    | List all available stacks            |
| `/grafana set-stack` | Set your default stack               |
| `/grafana escalate`  | Page a user or a team                |
| `/grafana incident`  | Prefix for Incident-related commands |

### Incident-related commands

| Command                                                | Description                           |
|--------------------------------------------------------|---------------------------------------|
| `/grafana incident new`                                | Create new incident                   |
| `/grafana incident new  “title”`                       | Create new incident with severity     |
| `/grafana incident list`                               | List all active incidents             |
| `/grafana incident roles`                              | Find out who’s involved               |
| `/grafana incident talk`                               | Set up a collaboration space          |
| `/grafana incident status`                             | Get a live inline update              |
| `/grafana incident severity`                           | Set the incident severity             |
| `/grafana incident severity major`                     | Update the incident severity to major |
| `/grafana incident tasks`                              | Create, assign and manage tasks       |
| `/grafana incident tasks help`                         | More information about tasks          |
| `/grafana incident task add 'deploy new release'`      | Add a new task                        |
| `/grafana incident task add 'deploy new release' @bob` | Add a new task and assign to @bob     |
| `/grafana incident tasks list`                         | View current tasks                    |
| `/grafana incident notes`                              | Add and view incident notes           |
| `/grafana incident notes help`                         | More information about notes          |
| `/grafana incident note add "customers notified"`      | Add a new note                        |
| `/grafana incident notes list`                         | View current notes                    |

## Permissions scope and purpose

The Grafana IRM Slack app only requests permissions that are essential to its proper function and integration with Slack.
Refer to the [Slack documentation](https://api.slack.com/scopes) for more information on permission scopes.

By granting access to the app, you are authorizing Grafana IRM the following permissions in your Slack workspace:

### Workspace and user access

| Permission         | Description                                                    | Purpose                                                                                        |
|--------------------|----------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| team:read          | View the workspace name, email domain, and icon                | Used for identification and to establish an association with your workspace                    |
| users:read         | View people in a workspace                                     | Used to find users by email and facilitate account matching between Grafana and your workspace |
| users.profile:read | View profile details about people in a workspace               | This permission enables us to fetch profile data, such as Slack handles and avatars            |
| users:write        | Set presence for Grafana IRM Slack app                         | Allows @GrafanaIRM to be added to your workspace                                               |
| usergroups:read    | View user groups in a workspace                                | Required to connect on-call schedules and escalation chains to Slack user groups               |
| usergroups:write   | Create and manage user groups                                  | Required to connect on-call schedule and escalation chains to Slack user groups                |
| incoming-webhook   | Create one-way webhooks to post messages to a specific channel | Used to display a channel picker in the installation sequence                                  |

### Public channel access

| Permission       | Description                                                                               | Purpose                                                                                                         |
|------------------|-------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| channels:read    | View basic information about public channels                                              | Used when adding a new channel to an escalation chain and to locate and update incident-specific channels       |
| channels:manage  | Manage public channels that Grafana IRM has been added to and create new ones             | Allows the app to create new channels and invite users to these channels                                        |
| channels:join    | Join public channels in a workspace                                                       | Allows @GrafanaIRM to join channels                                                                             |
| channels:history | View messages and other content in public channels that Grafana IRM has been added to     | Allows @GrafanaIRM to list messages in channels where the app has access to be included in the resolution notes |
| bookmarks:read   | List bookmarks                                                                            | Used to access bookmarks, such as PIR documents and Google Meet links, related to incidents                     |
| bookmarks:write  | Create, edit, and remove bookmarks                                                        | Necessary for managing incident-related bookmarks, including PIR documents and Google Meet links                |
| files:read       | View files shared in channels and conversations that Grafana IRM is a part of             | For incident-related file sharing and collaboration within authorized channels                                  |
| files:write      | Upload, edit, and delete files as Grafana IRM                                             | Used to upload image attachments so they appear in the Incident timeline                                        |
| pins:read        | View pinned content in channels and conversations that Grafana Incident has been added to | Used to access and display pinned content related to incidents                                                  |

### Private channel access

| Permission       | Description                                                                      | Purpose                                                                                                   |
|------------------|----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| groups:read      | View basic information about private channels that Grafana IRM has been added to | Used to access information from private incident-specific channels                                        |
| groups:write     | Manage private channels that Grafana IRM has been added to and create new ones   | Required to create private incident-specific channels for private incidents                               |
| groups:history   | List messages from private incident-specific channels                            | Allows @GrafanaIRM to list messages from private incident channels to be included in the resolution notes |
| usergroups:write | Create and manage user groups                                                    | Required for connecting on-call schedules to Slack user groups                                            |
| usergroups:read  | View user groups in a workspace                                                  | Required for connecting on-call schedules to Slack user groups                                            |

### Message and conversation access

| Permission           | Description                                                                                                        | Purpose                                                                                                                     |
|----------------------|--------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| app_mentions:read    | View messages and other content in public channels that Grafana IRM is a part of                                   | Enables the app to read messages and related content within authorized channels                                             |
| chat:write           | Post messages in approved channels & conversations                                                                 | Allows @GrafanaIRM to post messages to Slack                                                                                |
| chat:write.customize | Send messages as Grafana IRM with a customized username and avatar                                                 | Allows @GrafanaIRM to post messages to Slack                                                                                |
| chat:write.public    | Send messages to channels GrafanaI RM isn't a member of                                                            | Allows @Grafan IRM to post messages to Slack                                                                                |
| reaction:read        | View emoji reactions and their associated content in channels and conversations that Grafana IRM has been added to | Allows @GrafanaIRM to monitor message events for the 🤖 emoji to be included in the incident timeline                        |
| reaction:write       | Add and edit emoji reactions                                                                                       | Required to include messages with the 📝 emoji on resolution notes                                                           |
| im:read              | View basic information about direct messages that Grafana IRM has been added to                                    | Enables the app to send alert group notifications to users via direct message                                               |
| im:write             | Start direct messages with people                                                                                  | Used to notify users about alerts via direct message as well as invite users who create an incident to the incident channel |
| im:history           | View messages and other content in direct messages that Grafana IRM has been added to                              | Allows @GrafanaIRM to monitor message events in direct messages that it’s a part of                                         |
| mpim:history         | View messages and other content in group direct messages that Grafana IRM has been added to                        | Allows @GrafanaIRM to monitor message events in group direct messages that it’s a part of                                   |
