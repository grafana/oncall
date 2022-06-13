---
aliases:
  - /docs/grafana-cloud/oncall/open-source/
  - /docs/oncall/latest/open-source/
keywords:
  - Open Source
title: Open Source
weight: 100
---

# Open Source

We prepared three environments for OSS users:
- **Hobby** environment for local usage & playing around: [README.md](https://github.com/grafana/oncall#getting-started).
- **Development** environment for contributors: [DEVELOPER.md](https://github.com/grafana/oncall/blob/dev/DEVELOPER.md)
- **Production** environment for reliable cloud installation using Helm: [Production Environment](#production-environment)

## Production Environment

TBD

## Slack Setup

Grafana OnCall Slack integration use a lot of Slack API features: 
- Subscription on Slack events requires OnCall to be externally available and provide https endpoint. 
- You will need to register new Slack App.

1. Make sure your OnCall is up and running.

2. You need OnCall to be accessible through https. For development purposes we suggest using [localtunnel](https://github.com/localtunnel/localtunnel). For production purposes please consider setting up proper web server with HTTPS termination. For localtunnel: 
```bash
# Choose the unique prefix instead of pretty-turkey-83
# Localtunnel will generate an url, e.g. https://pretty-turkey-83.loca.lt
# it is referred as <ONCALL_ENGINE_PUBLIC_URL> below
lt --port 8000 -s pretty-turkey-83 --print-requests
```

3. If you use localtunnel, open your external URL and click "Continue" to allow requests to bypass the warning page.

4. [Create a Slack Workspace](https://slack.com/create) for development, or use your company workspace.

5. Go to https://api.slack.com/apps and click Create New App button

6. Select `From an app manifest` option and choose the right workspace

7. Copy and paste the following block with the correct <YOUR_BOT_NAME> and <ONCALL_ENGINE_PUBLIC_URL> fields

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

6. Go to your "OnCall" -> "Env Variables" and set:
    ```
    SLACK_CLIENT_OAUTH_ID = Basic Information -> App Credentials -> Client ID
    SLACK_CLIENT_OAUTH_SECRET = Basic Information -> App Credentials -> Client Secret
    SLACK_SIGNING_SECRET = Basic Information -> App Credentials -> Signing Secret
    SLACK_INSTALL_RETURN_REDIRECT_HOST = << OnCall external URL >>
    ```

7. Go to "OnCall" -> "ChatOps" -> "Slack" and install Slack Integration

8. All set!

## Telegram Setup

- Telegram integrations requires OnCall to be externally available and provide https endpoint. 
- Telegram integration in OnCall is designed for collaborative team work. It requires Telegram Group and a Telegram Channel (private) for alerts. 

1. Make sure your OnCall is up and running.

2. Respectfully ask [BotFather](https://t.me/BotFather) for a key, put it in `TELEGRAM_TOKEN` in "OnCall" -> "Env Variables".

3. Set `TELEGRAM_WEBHOOK_HOST` with your external url for OnCall. 

4. Go to "OnCall" -> "ChatOps" -> Telegram and enjoy!

## Grafana OSS-Cloud Setup

Grafana OSS could be connected to Grafana Cloud for heartbeat and SMS / Phone Calls. We tried our best in making Grafana OSS <-> Cloud self-explanatory. Check "Cloud" page in your OSS OnCall instance.

Please note that it's possible either to use Grafana Cloud either Twilio for SMS/Phone calls. 

## Twilio Setup

1. Make sure Grafana OSS <-> Cloud connector is disabled. Set `GRAFANA_CLOUD_NOTIFICATIONS_ENABLED` as False.
2. Check "OnCall" -> "Env Variables" and set all variables starting with `TWILIO_`
