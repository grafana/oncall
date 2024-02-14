---
title: Alert groups feed
menuTitle: Alert feed
description: Understand how to view and respond to alert groups in the Grafana OnCall mobile app.
weight: 300
keywords:
  - OnCall
  - Mobile app
  - iOS
  - Android
  - Alert group
  - Feed
canonical: https://grafana.com/docs/oncall/latest/manage/mobile-app/alert-groups-feed/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/manage/mobile-app/alert-groups-feed/
  - /docs/grafana-cloud/alerting-and-irm/oncall/mobile-app/alert-groups-feed/
  - ../../mobile-app/alert-groups-feed/ # /docs/oncall/<ONCALL_VERSION>/mobile-app/alert-groups-feed/
---

# Alert Groups feed

On the **Feed** page, you can view Alert groups, under two tabs:

- **Mine** shows Alert Groups that involve you in one way or another. E.g. because a notification went to you about it, or you resolved it.
- **All** shows all Alert Groups, including ones that may not be relevant to you.

You can filter by status via the **filter** button on the top right. We are working on an expansion for this filter, to filter by team, integration name, and more.

Tap on any Alert Group to go to the detailed view.
From this page, you have various options available to you.
You can open the alert group in Slack for further discussion and collaboration, as well as share the link to this specific alert group with others.
Additionally, you can take action on the alert group directly from this page. You have the ability to acknowledge, resolve, and silence the alert group.

> **Note:** You need to have sufficient permission to take action on the alert group.
> To learn more about Grafana OnCall user roles and permission,
> refer to [Manage users and teams for Grafana OnCall][].

<img src="/static/img/oncall/mobile-app-alertgroups.png" width="300px">
<img src="/static/img/oncall/mobile-app-alertgroup.png" width="300px">

{{% docs/reference %}}
[Manage users and teams for Grafana OnCall]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/manage/user-and-team-management#user-roles-and-permissions"
[Manage users and teams for Grafana OnCall]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/manage/user-and-team-management#user-roles-and-permissions"
{{% /docs/reference %}}
