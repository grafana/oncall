---
aliases:
  - ../../chat-options/configure-slack/
  - /docs/oncall/latest/integrations/chatops-integrations/configure-slack/
canonical: https://grafana.com/docs/oncall/latest/integrations/chatops-integrations/configure-slack/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - amixr
  - oncall
  - slack
title: Slack integration for Grafana OnCall
weight: 100
---

# Slack integration for Grafana OnCall

The Slack integration for Grafana OnCall incorporates your Slack workspace directly into your incident response workflow
to help your team focus on alert resolution with less friction.

Integrating your Slack workspace with Grafana OnCall allows users and teams to be notified of alerts directly in Slack
with automated alert escalation steps and user notification preferences. There are a number of alert actions that users
can take directly from Slack, including acknowledge, resolve, add resolution notes, and more.

## Before you begin

To install the Slack integration, you must have Admin permissions in your Grafana instance as well as the Slack workspace
that you’d like to integrate with.

For Open Source Grafana OnCall Slack installation guidance, refer to
[Open Source Grafana OnCall]({{< relref "../../../open-source/" >}}).

## Install Slack integration for Grafana OnCall

1. From the **ChatOps** tab in Grafana OnCall, select **Slack** in the side menu.
2. Click **Install Slack integration**.
3. Read the notice and agree to proceed to the Slack website.
4. Provide your Slack workspace URL and sign with your Slack credentials.
5. Click **Allow** to give Grafana OnCall permission to access your Slack workspace.

## Post-install configuration for Slack integration

Configure the following additional settings to ensure Grafana OnCall alerts are routed to the intended Slack channels
and users:

1. From your **Slack integration** settings, select a default slack channel in the first dropdown menu. This is where
   alerts will be sent unless otherwise specified in escalation chains.
2. In **Additional Settings**, configure alert reminders for alerts to retrigger after being acknowledged for some
   amount of time.
3. Ensure all users verify their slack account in their Grafana OnCall **users info**.

### Configure Escalation Chains with Slack notifications

Once your Slack integration is configured you can configure Escalation Chains to notify via Slack messages for alerts
in Grafana OnCall.

There are two Slack notification options that you can configure into escalation chains, notify whole Slack channel and
notify Slack user group:

1. In Grafana OnCall, navigate to the **Escalation Chains** tab then select an existing escalation chain or
   click **+ New escalation chain**.
2. Click the dropdown for **Add escalation step**.
3. Configure your escalation chain with automated Slack notifications.

### Configure user notifications with Slack mentions

To be notified of alerts in Grafana OnCall via Slack mentions:

1. Navigate to the **Users** tab in Grafana OnCall, click **Edit** next to a user.
2. In the **User Info** tab, edit or configure notification steps by clicking + Add Notification step
3. select **Notify by** in the first dropdown and select **Slack mentions** in the second dropdown to receive alert
   notifications via Slack mentions.

### Configure on-call notifications in Slack

The Slack integration for Grafana Oncall supports automated Slack on-call notifications that notify individuals and
teams of their on-call shifts. Admins can configure shift notification behavior in Notification preferences:

1. When an on-call shift notification is sent to a person or channel, click the gear icon to
   access **Notifications preferences**.
2. Configure on-call notifications for future shift notifications.
