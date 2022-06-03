+++
title = "Configure Telegram for Grafana OnCall"
keywords = ["Grafana Cloud", "Alerts", "Notifications", "on-call", "amixr", "oncall", "telegram"]
weight = 300
+++

# Configure Telegram for Grafana OnCall

You can use Telegram to deliver alert group notifications to a dedicated channel, and allow users to perform notification actions. 

Each alert group notification is assigned a dedicated discussion. Users can perform notification actions (acknowledge, resolve, silence), create reports, and discuss alerts in the comments section of the discussions.

## Connect to Telegram

Connect your organization's Telegram account to your Grafana OnCall instance by following the instructions provided in OnCall. You can use the following steps as a reference.

>**NOTE:** Only Grafana users with the administrator role can configure OnCall settings.

1. In OnCall, click on the **ChatOps** tab and select Telegram in the side menu.
1. Click **Connect Telegram channel** and follow the instructions, mirrored here for reference. A unique verification code will be generated that you must use to activate the channel.
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

## Configure Telegram user settings in OnCall

1. In your profile, find the Telegram setting and click **Connect**.
1. Click **Connect automatically** for the bot to message you and to bring up your telegram account.
1. Click **Start** when the OnCall bot messages you.

If you want to connect manually, you can click the URL provided and then **SEND MESSAGE**. In your Telegram account, click **Start**.