---
aliases:
  - /docs/oncall/latest/configure-user-settings/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - amixr
  - oncall
  - integrations
title: Manage users and teams for Grafana OnCall
canonical: "https://grafana.com/docs/oncall/latest/configure-user-setting/"
weight: 1300
---

# Manage users and teams for Grafana OnCall

Grafana OnCall is configured based on the teams you've created on the organization level of your Grafana instance, in **Configuration > Teams**. Administrators can create a different configuration for each team, and can navigate between team configurations in the **Select Team** dropdown menu in the **Incidents** section of Grafana OnCall.

Users can edit their contact information, but user permissions are assigned at the Cloud portal level.

## Configure user notification policies

Administrators can configure how each user will receive notifications when they are are scheduled to receive them in escalation chains. Users can verify phone numbers and email addresses.

> **NOTE**: You cannot add users or manage permissions in Grafana OnCall. Most user settings are found on the organizational level of your Grafana instance in **Configuration > Users**.

1. Find users.

   Select the **Users** tab and use the browser to search for a user in the team associated with the OnCall configuration.

1. Configure user settings.

   Add and verify a phone number, a Slack username, and a Telegram account if you want to receive notifications using these mediums.

   > **NOTE:** To edit a user's profile username, email, or role, you must do so in the **Users** tab in the **Configuration** menu of your Grafana instance.

1. Configure notification settings.

   Specify the notification medium and frequency for each user. Notification steps will be followed in the order they are listed.

   The settings you specify in **Default Notifications** dictate how a user is notified for most escalation thresholds.

   **Important Notifications** are labeled in escalation chains. If an escalation event is marked as an important notification, it will bypass **Default Notification** settings and notify the user by the method specified.

## Configure Telegram user settings in OnCall

1. In your profile, find the Telegram setting and click **Connect**.
1. Click **Connect automatically** for the bot to message you and to bring up your telegram account.
1. Click **Start** when the OnCall bot messages you.

If you want to connect manually, you can click the URL provided and then **SEND MESSAGE**. In your Telegram account, click **Start**.

## Configure Slack user settings in OnCall

1. In your profile, find the Slack setting and click **Connect**.
1. Follow the instructions to verify your account.
