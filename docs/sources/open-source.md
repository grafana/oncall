---
aliases:
  - /docs/grafana-cloud/oncall/open-source/
  - /docs/oncall/latest/open-source/
keywords:
  - Open Source
title: Open Source
weight: 300
---

# Grafana OnCall open source guide

Grafana OnCall is a developer-friendly incident response tool that's available to Grafana open source and Grafana Cloud users. The OSS version of Grafana OnCall provides the same reliable on-call management solution along with the flexibility of a self-managed environment. 

This guide describes the necessary installation and configuration steps needed to configure OSS Grafana OnCall.

## Install Grafana OnCall OSS

There are three Grafana OnCall OSS environments available:

- **Hobby** playground environment for local usage: [README.md](https://github.com/grafana/oncall#getting-started)
- **Development** environment for contributors: [DEVELOPER.md](https://github.com/grafana/oncall/blob/dev/DEVELOPER.md)
- **Production** environment for reliable cloud installation using Helm: [Production Environment](#production-environment)

## Production Environment
We suggest using our official helm chart for the reliable production deployment of Grafana OnCall. It will deploy Grafana OnCall engine and celery workers, along with RabbitMQ cluster, Redis Cluster, and the database. 

Check the [helm chart](https://github.com/grafana/oncall/tree/dev/helm/oncall) for more details. 

We'll always be happy to provide assistance with production deployment in [our communities](https://github.com/grafana/oncall#join-community)! 

## Update Grafana OnCall OSS
To update an OSS installation of Grafana OnCall, please see the update docs:
- **Hobby** playground environment: [README.md](https://github.com/grafana/oncall#update-version)
- **Production** Helm environment: [Helm update](https://github.com/grafana/oncall/tree/dev/helm/oncall#update)

## Slack Setup

The Slack integration for Grafana OnCall leverages Slack API features to provide a customizable and useful integration. Refer to the following steps to configure the Slack integration:

1. Ensure your Grafana OnCall environment is up and running.

1. Grafana OnCall must be accessible through HTTPS. For development purposes,  use [localtunnel](https://github.com/localtunnel/localtunnel). For production purposes, consider establishing a proper web server with HTTPS termination. 
For localtunnel, refer to the following configuration:

```bash
# Choose the unique prefix instead of pretty-turkey-83
# Localtunnel will generate an url, e.g. https://pretty-turkey-83.loca.lt
# it is referred as <ONCALL_ENGINE_PUBLIC_URL> below
lt --port 8080 -s pretty-turkey-83 --print-requests
```

1. If using localtunnel, open your external URL and click **Continue** to allow requests to bypass the warning page.

1. [Create a Slack Workspace](https://slack.com/create) for development, or use your company workspace.

1. Go to https://api.slack.com/apps and click **Create an App** .

1. Select `From an app manifest` option and select your workspace.

1. Replace the text with the following YAML code block . Be sure to replace `<YOUR_BOT_NAME>` and `<ONCALL_ENGINE_PUBLIC_URL>` fields with the appropriate information. 

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
      - name: Add to resolution note
        type: message
        callback_id: add_resolution_note
        description: Add this message to resolution note
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

1. Set environment variables by navigating to your Grafana OnCall, then click **Env Variables** and set the following:
    ```
    SLACK_CLIENT_OAUTH_ID = Basic Information -> App Credentials -> Client ID
    SLACK_CLIENT_OAUTH_SECRET = Basic Information -> App Credentials -> Client Secret
    SLACK_SIGNING_SECRET = Basic Information -> App Credentials -> Signing Secret
    SLACK_INSTALL_RETURN_REDIRECT_HOST = << OnCall external URL >>
    ```

1. In OnCall, navigate to **ChatOps**, select Slack and click **Install Slack integration**.

1. Configure additional Slack settings.

## Telegram Setup

The Telegram integration for Grafana OnCall is designed for collaborative team work and improved incident response. Refer to the following steps to configure the Telegram integration:

1. Ensure your OnCall environment is up and running.

1. Request [BotFather](https://t.me/BotFather) for a key, then add your key in `TELEGRAM_TOKEN` in your Grafana OnCall **Env Variables**.

1. Set `TELEGRAM_WEBHOOK_HOST` with your external URL for your Grafana OnCall. 

1. From the **ChatOps** tab in Grafana OnCall, click **Telegram**.

## Grafana OSS-Cloud Setup

The benefits of connecting to Grafana Cloud include:
- Cloud OnCall could monitor OSS OnCall uptime using heartbeat
- SMS for user notifications
- Phone calls for user notifications.

To connect to Grafana Cloud, refer to the **Cloud** page in your OSS Grafana OnCall instance.

## Twilio Setup

Grafana OnCall supports Twilio SMS and phone call notifications delivery. If you prefer to configure SMS and phone call notifications using Twilio, complete the following steps:

1. Set `GRAFANA_CLOUD_NOTIFICATIONS_ENABLED` as **False** to ensure the Grafana OSS <-> Cloud connector is disabled.
1. From your **OnCall** environment, select **Env Variables** and configure all variables starting with `TWILIO_`. 
