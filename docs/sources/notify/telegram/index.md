---
aliases:
  - ../../chat-options/configure-telegram/
  - /docs/oncall/latest/integrations/chatops-integrations/configure-telegram/
canonical: https://grafana.com/docs/oncall/latest/integrations/chatops-integrations/configure-telegram/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - amixr
  - oncall
  - telegram
title: Telegram
weight: 300
---

# NOT EDITED AFTER STRUCTURE CHANGE

# Telegram integration for Grafana OnCall

You can manage alerts either directly in your personal Telegram DMs or in a dedicated team channel.

## Configure Telegram user settings in Grafana OnCall

To receive alert group contents, escalation logs and to be able to perform actions (acknowledge, resolve, silence) in
Telegram DMs, please refer to the following steps:

1. In your profile, find the Telegram setting and click **Connect**.
1. Click **Connect automatically** for the bot to message you and to bring up your telegram account.
1. Click **Start** when the OnCall bot messages you and wait for the connection confirmation.
1. Done! Now you can receive alerts directly to your Telegram DMs.

If you want to connect manually, you can click the URL provided and then **SEND MESSAGE**. In your Telegram account,
click **Start**.

## (Optional) Connect to a Telegram channel

In case you want to manage alerts in a dedicated Telegram channel, please use the following steps as a reference.

> **NOTE:** Only Grafana users with the administrator role can configure OnCall settings.

1. In OnCall, click on the **ChatOps** tab and select Telegram in the side menu.
1. Click **Connect Telegram channel** and follow the instructions, mirrored here for reference. A unique verification
   code will be generated that you must use to activate the channel.
1. In your team Telegram account, create a new channel, and set it to **Private**.
1. In **Manage Channel**, make sure **Sign messages** is enabled.
1. Create a new discussion group.
   This group handles alert actions and comments.
1. Add the discussion group to the channel.
   In **Manage Channel**, click **Discussion** to find and add the new group.
1. In OnCall, click the link to the OnCall bot to add it to your contacts.
1. In Telegram, add the bot to your channel as an Admin. Allow it to **Post Messages**.
1. Add the bot to the discussion group.
1. In OnCall, send the provided verification code to the channel.
1. Make sure users connect to Telegram in their OnCall user profile.

Each alert group is assigned a dedicated discussion. Users can perform actions (acknowledge, resolve, silence), and
discuss alerts in the comments section of the discussions.
In case an integration route is not configured to use a Telegram channel, users will receive messages with alert group
contents, logs and actions in their DMs.
