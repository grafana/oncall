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
- **Production** environment for reliable cloud installation using Helm: #production

## Slack Setup

Grafana OnCall Slack integration use most of the features Slack API provides. 
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

2. [Create a Slack Workspace](https://slack.com/create) for development, or use your company workspace.

3. Go to https://api.slack.com/apps and click Create New App button

4. Select `From an app manifest` option and choose the right workspace

5. Copy and paste the following block with the correct <YOUR_BOT_NAME> and <ONCALL_ENGINE_PUBLIC_URL> fields

<details>
  <summary>Click to expand!</summary>

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
</details>

6. Click `Install to workspace` button to generate the credentials 

7. Populate the environment with variables related to Slack.

    Go to your OnCall plugin -> Env Variables and set:
    ```
    SLACK_CLIENT_OAUTH_ID = Basic Information -> App Credentials -> Client ID
    SLACK_CLIENT_OAUTH_SECRET = Basic Information -> App Credentials -> Client Secret
    SLACK_API_TOKEN = OAuth & Permissions -> Bot User OAuth Token
    SLACK_INSTALL_RETURN_REDIRECT_HOST = https://pretty-turkey-83.loca.lt
    ```

8. Set BASE_URL Env variable through web interface or edit `grafana-plugin/grafana-plugin.yml` to set `onCallApiUrl` fields with publicly available url:
    ```
        onCallApiUrl: https://pretty-turkey-83.loca.lt
    ```

9. For dev environment only: Edit grafana-plugin/src/plugin.json to add `Bypass-Tunnel-Reminder` header section for all existing routes 
    > this headers required for the local development only, otherwise localtunnel blocks requests from grafana plugin
 
    ```
        {
         "path": ...,
         ...
         "headers": [
           ...
           {
             "name": "Bypass-Tunnel-Reminder",
             "content": "True"
           }
         ]
       },
    ```
10. Rebuild the plugin
     ```
     yarn watch
     ```
11. Restart grafana instance

12. All set! Go to Slack and check if your application is functional.

