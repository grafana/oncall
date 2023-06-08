---
keywords:
  - Open Source
title: Open Source
weight: 400
---

# Grafana OnCall open source guide

Grafana OnCall is a developer-friendly incident response tool that's available to Grafana open source and Grafana Cloud
users. The OSS version of Grafana OnCall provides the same reliable on-call management solution along with the
flexibility of a self-managed environment.

This guide describes the necessary installation and configuration steps needed to configure OSS Grafana OnCall.

## Install Grafana OnCall OSS

There are three Grafana OnCall OSS environments available:

- **Hobby** playground environment for local usage: [README.md](https://github.com/grafana/oncall#getting-started)
- **Development** environment for contributors: [development README.md](https://github.com/grafana/oncall/blob/dev/dev/README.md)
- **Production** environment for reliable cloud installation using Helm: [Production Environment](#production-environment)

## Production Environment

We suggest using our official helm chart for the reliable production deployment of Grafana OnCall. It will deploy
Grafana OnCall engine and celery workers, along with RabbitMQ cluster, Redis Cluster, and the database.

> **Note:** The Grafana OnCall engine currently supports one instance of the Grafana OnCall plugin at a time.

Check the [helm chart](https://github.com/grafana/oncall/tree/dev/helm/oncall) for more details.

We'll always be happy to provide assistance with production deployment in [our communities](https://github.com/grafana/oncall#join-community)!

## Update Grafana OnCall OSS

To update an OSS installation of Grafana OnCall, please see the update docs:

- **Hobby** playground environment: [README.md](https://github.com/grafana/oncall#update-version)
- **Production** Helm environment: [Helm update](https://github.com/grafana/oncall/tree/dev/helm/oncall#update)

## Slack Setup

The Slack integration for Grafana OnCall leverages Slack API features to provide a customizable and useful integration.
Refer to the following steps to configure the Slack integration:

1. Ensure your Grafana OnCall environment is up and running.

1. Grafana OnCall must be accessible through HTTPS. For development purposes, use [localtunnel](https://github.com/localtunnel/localtunnel).
   For production purposes, consider establishing a proper web server with HTTPS termination.
   For localtunnel, refer to the following configuration:

```bash
# Choose the unique prefix instead of pretty-turkey-83
# Localtunnel will generate an url, e.g. https://pretty-turkey-83.loca.lt
# it is referred as <ONCALL_ENGINE_PUBLIC_URL> below
lt --port 8080 -s pretty-turkey-83 --print-requests
```

1. If using localtunnel, open your external URL and click **Continue** to allow requests to bypass the warning page.

1. [Create a Slack Workspace](https://slack.com/create) for development, or use your company workspace.

1. Go to <https://api.slack.com/apps> and click **Create an App** .

1. Select `From an app manifest` option and select your workspace.

1. Replace the text with the following YAML code block . Be sure to replace `<YOUR_BOT_NAME>` and `<ONCALL_ENGINE_PUBLIC_URL>`
   fields with the appropriate information.

```yaml
_metadata:
  major_version: 1
  minor_version: 1
display_information:
  name: <YOUR_BOT_NAME>
features:
  app_home:
    home_tab_enabled: false
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
      description: Create a manual alert group
      should_escape: false
    - command: /escalate
      url: <ONCALL_ENGINE_PUBLIC_URL>/slack/interactive_api_endpoint/
      description: Direct page user(s) or schedule(s)
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
      - user_profile_changed
  interactivity:
    is_enabled: true
    request_url: <ONCALL_ENGINE_PUBLIC_URL>/slack/interactive_api_endpoint/
  org_deploy_enabled: false
  socket_mode_enabled: false
```

1. Set environment variables by navigating to your Grafana OnCall, then click **Env Variables** and set the following:

   ```text
   SLACK_CLIENT_OAUTH_ID = Basic Information -> App Credentials -> Client ID
   SLACK_CLIENT_OAUTH_SECRET = Basic Information -> App Credentials -> Client Secret
   SLACK_SIGNING_SECRET = Basic Information -> App Credentials -> Signing Secret
   SLACK_INSTALL_RETURN_REDIRECT_HOST = << OnCall external URL >>
   ```

1. In OnCall, navigate to **ChatOps**, select Slack and click **Install Slack integration**.

1. Configure additional Slack settings.

## Telegram Setup

The Telegram integration for Grafana OnCall is designed for collaborative team work and improved incident response.
Refer to the following steps to configure the Telegram integration:

1. Ensure your Grafana OnCall environment is up and running.
2. Create a Telegram bot using [BotFather](https://t.me/BotFather) and save the token provided by BotFather. Please make
   sure to disable **Group Privacy** for the bot (Bot Settings -> Group Privacy -> Turn off).
3. Paste the token provided by BotFather to the `TELEGRAM_TOKEN` variable on the **Env Variables** page of your
   Grafana OnCall instance.
4. Set the `TELEGRAM_WEBHOOK_HOST` variable to the external address of your Grafana OnCall instance. Please note
   that `TELEGRAM_WEBHOOK_HOST` must start with `https://` and be publicly available (meaning that it can be reached by
   Telegram servers). If your host is private or local, consider using a reverse proxy (e.g. [ngrok](https://ngrok.com)).
5. Now you can connect Telegram accounts on the **Users** page and receive alert groups to Telegram direct messages.
   Alternatively, in case you want to connect Telegram channels to your Grafana OnCall environment, navigate
   to the **ChatOps** tab.

## Grafana OSS-Cloud Setup

The benefits of connecting to Grafana Cloud include:

- Cloud OnCall could monitor OSS OnCall uptime using heartbeat
- SMS for user notifications
- Phone calls for user notifications.

To connect to Grafana Cloud, refer to the **Cloud** page in your OSS Grafana OnCall instance.

## Twilio Setup

Grafana OnCall supports Twilio SMS and phone call notifications delivery. If you prefer to configure SMS and phone call
notifications using Twilio, complete the following steps:

1. Set `GRAFANA_CLOUD_NOTIFICATIONS_ENABLED` as **False** to ensure the Grafana OSS <-> Cloud connector is disabled.
1. From your **OnCall** environment, select **Env Variables** and configure all variables starting with `TWILIO_`.

## Email Setup

Grafana OnCall is capable of sending emails using SMTP as a user notification step. To setup email notifications, populate
the following env variables with your SMTP server credentials:

- `EMAIL_HOST` - SMTP server host
- `EMAIL_HOST_USER` - SMTP server user
- `EMAIL_HOST_PASSWORD` - SMTP server password
- `EMAIL_PORT` (default is `587`) - SMTP server port
- `EMAIL_USE_TLS` (default is `True`) - To enable/disable TLS
- `EMAIL_FROM_ADDRESS` (optional) - Email address used to send emails. If not specified, `EMAIL_HOST_USER` will be used.

After enabling the email integration, it will be possible to use the `Notify by email` notification step in user settings.

## Inbound Email Setup

Grafana OnCall is capable of creating alert groups from
[Inbound Email integration]({{< relref "../integrations/inbound-email" >}}).

To configure Inbound Email integration for Grafana OnCall OSS populate env variables with your Email Service Provider data:

- `INBOUND_EMAIL_ESP` - Inbound email ESP name. Available options: `amazon_ses`, `mailgun`, `mailjet`, `mandrill`, `postal`, `postmark`, `sendgrid`, `sparkpost`
- `INBOUND_EMAIL_DOMAIN` - Inbound email domain
- `INBOUND_EMAIL_WEBHOOK_SECRET` - Inbound email webhook secret

You will also need to configure your ESP to forward messages to the following URL: `<ONCALL_ENGINE_PUBLIC_URL>/integrations/v1/inbound_email_webhook`.

## Limits

By default, Grafana OnCall limits email and phone notifications (calls, SMS) to 200 per user per day.
The limit can be changed using env variables:

- `PHONE_NOTIFICATIONS_LIMIT` (default is `200`) - phone notifications per user
- `EMAIL_NOTIFICATIONS_LIMIT` (default is `200`) - emails per user

## Mobile application set up

> **Note**: This application is currently in beta

Grafana OnCall OSS users can use the mobile app to receive push notifications from OnCall.
Grafana OnCall OSS relies on Grafana Cloud as on relay for push notifications.
You must first connect your Grafana OnCall OSS to Grafana Cloud for the mobile app to work.

Refer to [Grafana OSS-Cloud Setup]({{< relref "_index.md#grafana-oss-cloud-setup" >}}) in this document before continuing with the mobile app.

For Grafana OnCall OSS, the mobile app QR code includes an authentication token along with a backend URL.
Your Grafana OnCall OSS instance should be reachable from the same network as your mobile device, preferably from the internet.

For more information, see [Grafana OnCall mobile app]({{< relref "../mobile-app" >}})

## Alert Group Escalation Auditor

Grafana OnCall has a periodic background task, which runs to check that all alert group escalations have finished
properly. This feature, if configured, can also ping an OnCall Webhook Integration's heartbeat URL, so that you can be
alerted, in the event that something goes wrong.

Logs originating from the celery worker, for the `apps.alerts.tasks.check_escalation_finished.check_escalation_finished_task`
task, that reference a `AlertGroupEscalationPolicyExecutionAuditException` exception
indicate that the auditor periodic task is failing check(s) on one or more alert groups. Logs for this task which
mention `.. passed the audit checks` indicate that there were no issues with with the escalation on the audited
alert groups.

To configure this feature as such:

1. Create a Webhook, or Formatted Webhook, Integration type.
1. Under the "Heartbeat" tab in the Integration modal, copy the unique heartbeat URL that is shown.
1. Set the hearbeat's expected time interval to 15 minutes (see note below regarding `ALERT_GROUP_ESCALATION_AUDITOR_CELERY_TASK_HEARTBEAT_INTERVAL`)
1. Configure the integration's escalation chain as necessary
1. Populate the following env variables:

- `ALERT_GROUP_ESCALATION_AUDITOR_CELERY_TASK_HEARTBEAT_URL` - integration's unique heartbeat URL
- `ALERT_GROUP_ESCALATION_AUDITOR_CELERY_TASK_HEARTBEAT_INTERVAL` - how often the auditor task should run. By default the
  task runs every 13 minutes so we therefore recommend setting the heartbeat's expected time interval to 15 minutes. If you
  would like to modify this, we recommend configuring this env variable to 1 or 2 minutes less than the value set for the
  integration's heartbeat expected time interval.
