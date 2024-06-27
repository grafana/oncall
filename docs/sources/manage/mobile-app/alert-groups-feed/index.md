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
refs:
  manage-users-and-teams-for-grafana-oncall:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/user-and-team-management/#user-roles-and-permissions
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/user-and-team-management/#user-roles-and-permissions
---

# Alert Groups feed

On the **Feed** page, you can view Alert groups, under two tabs:

- **Mine** shows Alert Groups that involve you in one way or another. E.g. because a notification went to you about it, or you resolved it.
- **All** shows all Alert Groups, including ones that may not be relevant to you.

You can filter by status via the **filter** button on the top right.

Tap on any Alert Group to go to the detailed view.
From this page, you have various options available to you.

You can browse the grouped alerts as well as the escalation chain used for the alert group and the timeline.
You can invite other participants, open the alert group in Slack for further discussion and collaboration,
as well as share the link to this specific alert group with others.
Additionally, you can take action on the alert group directly from this page. You have the ability to acknowledge, resolve, and silence the alert group.

> **Note:** You need to have sufficient permission to take action on the alert group.
> To learn more about Grafana OnCall user roles and permission,
> refer to [Manage users and teams for Grafana OnCall](ref:manage-users-and-teams-for-grafana-oncall).

<img src="/static/img/oncall/mobile-app-alertgroups2.png" width="300px">
<img src="/static/img/oncall/mobile-app-alertgroup2.png" width="300px">
<img src="/static/img/oncall/mobile-app-timeline.png" width="300px">
