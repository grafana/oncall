---
title: Mattermost
menuTitle: Mattermost
description: How to connect Mattermost for alert group notifications.
weight: 900
keywords:
  - OnCall
  - Notifications
  - ChatOps
  - Mattermost
canonical: https://grafana.com/docs/oncall/latest/manage/notify/mattermost/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/manage/notify/mattermost/
  - /docs/grafana-cloud/alerting-and-irm/oncall/notify/mattermost/
  - ../../chat-options/configure-mattermost
---

# Mattermost integration for Grafana OnCall

The Mattermost integration for Grafana OnCall allows connecting a Mattermost channel directly
into your incident response workflow to help your team focus on alert resolution with less friction.

At the moment, this integration is only available for OSS installations.

## Before you begin

To install the Mattermost integration, you must have Admin Permissions in your Grafana setup
as well as in the Mattermost instance that you'd like to integrate with.

Follow the steps in our [documentation](https://grafana.com/docs/oncall/latest/open-source/#mattermost-setup).

## Connect to a Mattermost Channel

1. Go to the Mattermost channel you want to connect to, check its information and copy the channel id.
2. In Grafana OnCall, in the Settings section, click on the **ChatOps** tab and select Mattermost in the side menu.
3. Click the **Add Mattermost channel** button, paste the channel id from step (1) and click **Create**.
4. Set a default channel for the alerts.

(Note: Make sure the bot in your setup is member of the team the channel belongs to and
has `read_channel` privileges [Ref](https://api.mattermost.com/#tag/channels/operation/GetChannelByNameForTeamName))
