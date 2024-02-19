---
title: Notifications
menuTitle: Notifications
description: Configure notifications and ChatOps integrations for Grafana OnCall.
weight: 200
keywords:
  - OnCall
  - Notifications
  - ChatOps
  - Slack
  - MS Teams
  - Telegram
  - Phone
canonical: https://grafana.com/docs/oncall/latest/manage/notify/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/manage/notify/
  - /docs/grafana-cloud/alerting-and-irm/oncall/notify/
  - ../notify/ # /docs/oncall/<ONCALL_VERSION>/notify/
---

# Notifications

Grafana OnCall directly supports the export of alert notifications to some popular messaging applications like Slack and
Telegram.
You can use [Outgoing webhooks][] for applications that aren't directly supported.

To configure supported messaging apps, refer to the following topics:

{{< section >}}

## Configure user notification policies

Notification policies are a configurable set of notification steps that determine how you're notified of alert in OnCall. Users with the Admin or Editor role are
able to receive notifications.
Users can verify phone numbers and email addresses in the **Users** tab of Grafana OnCall.

- **Default Notifications** dictate how a user is notified for most escalation thresholds.

- **Important Notifications** are labeled in escalation chains. If an escalation event is marked as an important notification,
it will bypass **Default Notification** settings and notify the user by the method specified.

> **NOTE**: You cannot add users or manage permissions in Grafana OnCall. User settings are found on the
> organizational level of your Grafana instance in **Configuration > Users**.

To configure a users notification policy:

1. Navigate to the **Users** tab of Grafana OnCall and search for or select a user.

1. Click **Edit** to the right of a user to open the **User Info** window.

1. Verify that there is a valid and verified phone number, along with ChatOps accounts in order to receive notifications via those methods.

1. Click **Add notification step** and use the dropdowns to specify the notification method and frequency. Notification steps will be followed in the order they
are listed.

{{% docs/reference %}}
[Outgoing webhooks]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/outgoing-webhooks"
[Outgoing webhooks]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/outgoing-webhooks"
{{% /docs/reference %}}
