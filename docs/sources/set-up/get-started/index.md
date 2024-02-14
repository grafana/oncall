---
title: Get started with Grafana OnCall
menuTitle: Get started
description: A Guide for getting started with Grafana OnCall in Grafana Cloud
weight: 100
keywords:
  - Get started
  - OnCall
  - Configure
  - Escalation chains
  - Integrations
  - On-call schedules
canonical: https://grafana.com/docs/oncall/latest/set-up/get-started/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/set-up/get-started/
  - /docs/grafana-cloud/alerting-and-irm/oncall//get-started/
  - ../getting-started/ # /docs/oncall/<ONCALL_VERSION>/getting-started/
  - ../get-started/ # /docs/oncall/<ONCALL_VERSION>/get-started/
---

# Get started with Grafana OnCall

Grafana OnCall was built to help DevOps and SRE teams improve their on-call management process and resolve incidents faster. With OnCall,
users can create and manage on-call schedules, automate escalations, and monitor incident response from a central view, right within
the Grafana UI. Teams no longer have to manage separate alerts from Grafana, Prometheus, and Alertmanager, lowering the risk of
missing an important update and limiting the time spent receiving and responding to notifications.

With a centralized view of all your alerts and alert groups, automated escalations and grouping, and on-call scheduling, Grafana
OnCall helps ensure that alert notifications reach the right people, at the right time using the right notification method.

The following diagram details an example alert workflow with Grafana OnCall:

<img src="/static/img/docs/oncall/oncall-alert-workflow.png" class="no-shadow" width="700px">

These procedures introduce you to initial Grafana OnCall configuration steps, including monitoring system integration,
how to set up escalation chains, and how to set up calendar for on-call scheduling.

## Grafana Cloud OnCall vs Open Source Grafana OnCall

Grafana OnCall is available both in Grafana Cloud and Grafana Open Source.

OnCall is available in Grafana Cloud automatically:

1. Create or log in into [Grafana Cloud account](/auth/sign-up/create-user)
2. Sign in to your Grafana stack
3. Choose **Alerts and IRM** from the left menu
4. Click **OnCall** to access Grafana OnCall

Otherwise, to install Grafaana OnCall, refer to [Install Grafana OnCall OSS][].

## How to configure Grafana OnCall

* Users with [Admin role][user-and-team-management] can configure Alert rules (Integrations, Routes, etc)
to define **when and which users to notify**
* OnCall users with [Editor role][user-and-team-management] can work with Alerts Groups and set up personal settings,
e.g. **how to notify**.

> **Note:** If your role is **Editor**, you can skip to [Learn about the Alert Workflow](#learn-about-the-alert-workflow).

## Get alerts into Grafana OnCall and configure rules

Once you’ve installed Grafana OnCall, or accessed it from your Grafana Cloud instance, you can begin integrating with
monitoring systems to get alerts into Grafana OnCall. Additionally, you can configure when, and which, users get notified, by setting templates, routes,
escalation chains, etc.

### Integrate with a monitoring system

Regardless of where your alerts originate, you can send them to Grafana OnCall via available integrations or customizable
webhooks. To start receiving alerts in Grafana OnCall, use the following steps to configure your first integration and
send a demo alert.

#### Configure your first integration

1. In Grafana OnCall, navigate to the **Integrations** tab and click **+ New integration**.
2. Select an integration from the provided options, if the integration you’re looking for isn’t listed, then select Webhook.
3. Click **How to connect** to view the instructions specific to your monitoring system

#### Send a demo alert

1. In the integration tab, click **Send demo alert**, review and modify the alert payload as needed, and click **Send**
2. Navigate to the **Alert Groups** tab to see your test alert firing
3. Explore the Alert Group by clicking on the title
4. Acknowledge and resolve the test alert group

For more information on Grafana OnCall integrations and further configuration guidance, refer to
[Grafana OnCall integrations][integrations]

### Review and modify alert templates

Review and customize templates to interpret monitoring alerts and minimize noise. Group alerts, enable auto-resolution,
customize visualizations and notifications by extracting data from alerts. See more details in the
[Jinja2 templating][] section.

### Configure Escalation Chains

Escalation Chains are a set of steps that define who to notify, and when.

For more information, refer to [Escalation chains][].

Escalation Chains are customizable automated alert routing steps that enable you to specify who is notified for a certain
alert. In addition to escalation chains, you can configure Routes to send alerts to different escalation chains depending
on the alert details.

Once your integration is configured, you can set up an escalation chain to determine how alerts from your integration
are handled. Multi-step escalation chains help ensure thorough alert escalation to prevent alerts from being missed.

To configure Escalation Chains:

1. Navigate to the **Escalation Chains** tab and click **+ New Escalation Chain**
2. Give your Escalation Chain a useful name and click **Create**
3. Add a series of escalation steps from the available dropdown options.
4. To link your Escalation Chain to your integration, navigate back to the **Integrations tab**, Select your newly
   created Escalation Chain from the “**Escalate to**” dropdown.

Alerts from this integration will now follow the escalation steps configured in your Escalation Chain.

For more information on Escalation Chains and more ways to customize them, refer to [Escalation chains][]

Routes define which messenger channels and escalation chains to use for notifications.
For more information, refer to [Routes][].

### Learn about the Alert Workflow

* All Alerts in OnCall are grouped into Alert Groups.
An Alert Group can have the following, mutually exclusive states:
* **Firing:** Once Alert Group is registered, Escalation Policy associated with it is getting started.
Escalation policy will work while Alert Group is in this status.
* **Acknowledged:** Ongoing Escalation Chain will be interrupted. Unacknowledge will move Alert Group to
the "Firing" state and will re-launch Escalation Chain.
* **Silenced:** Similar to "Acknowledged" but designed to be temporary with a timeout. Once time is out, will
re-launch Escalation Chain and move Alert Group
  to the "Firing" state.
* **Resolved:** Similar to "Acknowledged".

**Possible transitions**:

* Firing -> Acknowledged
* Firing -> Silenced
* Firing -> Resolved
* Silenced -> Firing
* Silenced -> Acknowledged
* Silenced -> Resolved
* Acknowledged -> Silenced
* Acknowledged -> Firing
* Acknowledged -> Resolved
* Resolved -> Firing

Transition changes trigger Escalation Chains to launch, with a few-second delay (to avoid unexpected notifications).

## Get notified of an alert

In order for Grafana OnCall to notify you of an alert, you must configure how you want to be notified. Personal notification
policies, chatops integrations, and on-call schedules allow you to automate how users are notified of alerts.

### Configure personal notification policies

Personal notification policies determine how a user is notified for a certain type of alert. Get notified by SMS,
phone call, Slack mentions, or mobile push notification. Administrators can configure how users receive notifications
for certain types of alerts.
For more information on personal notification policies, refer to
[Manage users and teams for Grafana OnCall][user-and-team-management]

To configure users personal notification policies:

1. Navigate to the **Users** tab in Grafana OnCall
2. Select a user from the user list and click **Edit**
3. Configure **Default Notifications** and **Important Notification**

### Configure Slack for Grafana OnCall

Grafana OnCall integrates closely with your Slack workspace to deliver alert notifications to individuals, user groups,
and channels. Slack notifications can be triggered by steps in an escalation chain or as a step in users personal
notification policies.

To configure Slack for Grafana OnCall:

1. In OnCall, click on the ChatOps tab and select Slack in the side menu.
2. Click Install Slack integration.
3. Read the notice and confirm to proceed to the Slack website.
4. Sign in to your organization's Slack workspace.
5. Click Allow to allow Grafana OnCall to access Slack.
6. Ensure users verify their Slack accounts in their user profile in Grafana OnCall.

For further instruction on connecting to your Slack workspace, refer to
[Slack integration for Grafana OnCall][]

Grafana OnCall also supports other ChatOps integration like Microsoft Teams and Telegram.
For a full list of supported integrations, refer to [Notify people][].

### Add your on-call schedule

Grafana OnCall allows you to manage your on-call schedule in your preferred calendar app such as Google Calendar or
Microsoft Outlook.

To integrate your on-call calendar with Grafana OnCall:

1. In the **Schedules** tab of Grafana OnCall, click **+ Add team schedule for on-call rotation**.
2. Provide a schedule name.
3. Configure the rest of the schedule settings and click Create Schedule

For more information about OnCall schedules, refer to [On-call schedules][].

{{% docs/reference %}}
[escalation-chains-and-routes]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/escalation-chains-and-routes"
[escalation-chains-and-routes]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/escalation-chains-and-routes"

[Escalation chains]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/escalation-chains-and-routes#escalation-chains"
[Escalation chains]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/escalation-chains-and-routes#escalation-chains"

[integrations]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/integrations"
[integrations]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/integrations"

[Jinja2 templating]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating"
[Jinja2 templating]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating"

[Notify people]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/manage/notify"
[Notify people]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/manage/notify"

[On-call schedules]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/manage/on-call-schedules"
[On-call schedules]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/manage/on-call-schedules"

[Install Grafana OnCall OSS]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/set-up/open-source#install-grafana-oncall-oss"
[Install Grafana OnCall OSS]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/set-up/open-source#install-grafana-oncall-oss"

[Routes]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/escalation-chains-and-routes#routes"
[Routes]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/escalation-chains-and-routes#routes"

[Slack integration for Grafana OnCall]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/manage/notify/slack"
[Slack integration for Grafana OnCall]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/manage/notify/slack"

[user-and-team-management]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/manage/user-and-team-management"
[user-and-team-management]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/manage/user-and-team-management"
{{% /docs/reference %}}
