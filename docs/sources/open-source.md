---
aliases:
  - /docs/grafana-cloud/oncall/open-source/
  - /docs/oncall/latest/open-source/
keywords:
  - Open Source
title: Open Source
canonical: "https://grafana.com/docs/oncall/latest/open-source/"
weight: 300
---

# Grafana OnCall Open Source guide

Grafana OnCall is a developer-friendly incident response tool that is available to Grafana OSS users. 

This document is meant to guide you through open source specific Grafana OnCall configuration steps. 

There are three Grafana OnCall environments available for OSS users:

- **Hobby** Playground environment for local usage: [README.md](https://github.com/grafana/oncall#getting-started).
- **Development** environment for contributors: [DEVELOPER.md](https://github.com/grafana/oncall/blob/dev/DEVELOPER.md)
- **Production** environment for reliable cloud installation using Helm: [Production Environment](#production-environment)


## Configure Slack for OSS Grafana OnCall

The Slack integration for Grafana OnCall Slack leverages Slack API features for a customizable and useful integration.

The following are required to configure Slack for open source Grafana OnCall:
- Register a new Slack App.
- Grafana OnCall must be externally available and provide https endpoint to establish subscription on Slack events.

1. Make sure your Grafana OnCall environment is up and running.


2. OnCall must be accessible through https. For development purposes, it's recommended to use [localtunnel](https://github.com/localtunnel/localtunnel). For production purposes please consider setting up proper web server with HTTPS termination. 
Refer to the following example configuration for localtunnel: 

    ```bash
    # Choose the unique prefix instead of pretty-turkey-83
    # Localtunnel will generate an url, e.g. https://pretty-turkey-83.loca.lt
    # it is referred as <ONCALL_ENGINE_PUBLIC_URL> below
    lt --port 8000 -s pretty-turkey-83 --print-requests
    ```

1. If using localtunnel, open your external URL and click **Continue** to allow requests to bypass the warning page.

2. [Create a Slack Workspace](https://slack.com/create) or for development, or use your company workspace.

3. Go to https://api.slack.com/apps and click **Create New App**.

4. Select **`From an app manifest`** option and select your workspace.

5. Copy and paste the following block. Be sure to replace <YOUR_BOT_NAME> and <ONCALL_ENGINE_PUBLIC_URL> fields with the appropriate information. 

  ```yaml
  _metadata:
    major_version: 1
    minor_version: 1
  display_information:
    name: <YOUR_BOT_NAME>
  features:
    app_home:
      home_tab_enabled: true
      messages_tab_enabled: true
      messages_tab_read_only_enabled: false
    bot_user:
      display_name: <YOUR_BOT_NAME>
      always_online: true
    shortcuts:
      - name: Create a new incident
        type: message
        callback_id: incident_create
        description: Creates a new OnCall incident
      - name: Add to postmortem
        type: message
        callback_id: add_postmortem
        description: Add this message to postmortem
    slash_commands:
      - command: /oncall
        url: <ONCALL_ENGINE_PUBLIC_URL>/slack/interactive_api_endpoint/
        description: oncall
        should_escape: false
  oauth_config:
    redirect_urls:
      - <ONCALL_ENGINE_PUBLIC_URL>/api/internal/v1/complete/slack-install-free/
      - <ONCALL_ENGINE_PUBLIC_URL>/api/internal/v1/complete/slack-login/
    scopes:
      user:
        - channels:read
        - chat:write
        - identify
        - users.profile:read
      bot:
        - app_mentions:read
        - channels:history
        - channels:read
        - chat:write
        - chat:write.customize
        - chat:write.public
        - commands
        - files:write
        - groups:history
        - groups:read
        - im:history
        - im:read
        - im:write
        - mpim:history
        - mpim:read
        - mpim:write
        - reactions:write
        - team:read
        - usergroups:read
        - usergroups:write
        - users.profile:read
        - users:read
        - users:read.email
        - users:write
  settings:
    event_subscriptions:
      request_url: <ONCALL_ENGINE_PUBLIC_URL>/slack/event_api_endpoint/
      bot_events:
        - app_home_opened
        - app_mention
        - channel_archive
        - channel_created
        - channel_deleted
        - channel_rename
        - channel_unarchive
        - member_joined_channel
        - message.channels
        - message.im
        - subteam_created
        - subteam_members_changed
        - subteam_updated
        - user_change
    interactivity:
      is_enabled: true
      request_url: <ONCALL_ENGINE_PUBLIC_URL>/slack/interactive_api_endpoint/
    org_deploy_enabled: false
    socket_mode_enabled: false
  ```

6. Set environment variables by navigating to your Grafana OnCall, then click **Env Variables** and set the following:

    ```bash
    SLACK_CLIENT_OAUTH_ID = Basic Information -> App Credentials -> Client ID
    SLACK_CLIENT_OAUTH_SECRET = Basic Information -> App Credentials -> Client Secret
    SLACK_SIGNING_SECRET = Basic Information -> App Credentials -> Signing Secret
    SLACK_INSTALL_RETURN_REDIRECT_HOST = << OnCall external URL >>
    ```

7. From **OnCall**, navigate to **ChatOps**, select **Slack** and install Slack integration.

## Configure Telegram for OSS Grafana OnCall 

The Telegram integration for Grafana OnCall is designed for collaborative team work and improved incident response. 

The following is required to configure the Telegram integration for OSS OnCall:

- Grafana OnCall must be externally available and provide https endpoint to establish connection to Telegram.
- Telegram requires a separate, private Telegram Group and Telegram Channel for OnCall alerts to be sent to. 

1. Make sure your Grafana OnCall environment is up and running.

2. Request [BotFather](https://t.me/BotFather) for a key, then add the key in `TELEGRAM_TOKEN` in Grafana OnCall by navigating to **Env Variables**.

3. Set `TELEGRAM_WEBHOOK_HOST` with your external URL for Grafana OnCall. 

4. From the **ChatOps** tab in Grafana OnCall, click **Telegram** and your integration is now ready for use. 

## Configure Grafana Cloud for OnCall OSS 

Open source Grafana OnCall can be connected to Grafana Cloud to configure heartbeat notification as well as SMS and phone calls for user notifications.For more information, refer to the "Cloud" page in your OSS Grafana OnCall instance.

>**NOTE:** Phone call and SMS notifications can be configured using Grafana Cloud or you can use Twilio as an alternative option.

## Configure OSS Grafana OnCall notifications with Twilio

1. Set `GRAFANA_CLOUD_NOTIFICATIONS_ENABLED` as False to ensure the Grafana OSS <-> Cloud connector is disabled.
2. From your OnCall environment, select **Env Variables** and configure all variables starting with `TWILIO_`. 
