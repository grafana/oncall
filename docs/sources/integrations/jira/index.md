---
aliases:
  - jira/
  - /docs/oncall/latest/integrations/available-integrations/configure-jira/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-jira/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - Jira
title: Jira
weight: 500
---

# Jira integration for Grafana OnCall

The Jira integration for Grafana OnCall handles issue events sent from Jira webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin][user-and-team-management] to be able to create integrations in Grafana OnCall.

## Configuring Grafana OnCall to Receive Alerts from Jira

1. In the **Integrations** tab, click **+ New integration**.
2. Select **Jira** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section. You will need it when configuring Jira.

## Configuring Jira to Send Alerts to Grafana OnCall

Create a new webhook connection in Jira to send events to Grafana OnCall using the integration URL above.

Refer to [Jira documentation](https://developer.atlassian.com/server/jira/platform/webhooks/) for more information on how to create and manage webhooks

When creating a webhook in Jira, select the following events to be sent to Grafana OnCall:

1. Issue - created
2. Issue - updated
3. Issue - deleted
After setting up the connection, you can test it by creating a new issue in Jira. You should see a new alert group in Grafana OnCall.

## Grouping, auto-acknowledge and auto-resolve

Grafana OnCall provides grouping, auto-acknowledge and auto-resolve logic for the Jira integration:

- Alerts created from issue events are grouped by issue key
- Alert groups are auto-acknowledged when the issue status is set to "work in progress"
- Alert groups are auto-resolved when the issue is closed or deleted

To customize this behaviour, consider modifying alert templates in integration settings.

{{% docs/reference %}}
[user-and-team-management]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
[user-and-team-management]: "/docs/grafana-cloud/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
{{% /docs/reference %}}
