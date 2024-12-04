---
title: Mattermost
menuTitle: Mattermost
description: Explains that a Mattermost integration is not implemented yet.
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

The Mattermost integration for Grafana OnCall incorporates your mattermost channel directly into your incident response workflow to help your team focus on alert resolution with less friction

## Before you begin
To install the Mattermost integration, you must have Admin Permissions in your Grafana instance as well as the Mattermost instance that you'd like to integrate.

Follow the setup [documentation](https://grafana.com/docs/oncall/latest/open-source/#mattermost-setup)

## Connect to a Mattermost Channel
1. Navigate to the mattermost channel you want to integrate and click on the info icon and copy the channel id.
2. In OnCall, click on the **ChatOps** tab and select Mattermost in the side menu.
3. Click **Add Mattermost channel** button and paste the channel id from (1) and click **Create**
4. Choose a default channel for the alerts.

(Note: Make sure the bot created as part of setup is added to the team the channel is part of and has `read_channel` privilages [Ref](https://api.mattermost.com/#tag/channels/operation/GetChannelByNameForTeamName))


Please join [GitHub Issue](https://github.com/grafana/oncall/issues/96) or
check [PR](https://github.com/grafana/oncall/pull/606).
