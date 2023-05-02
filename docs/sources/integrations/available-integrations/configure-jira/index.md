---
aliases:
  - add-jira/
  - /docs/oncall/latest/integrations/available-integrations/configure-jira/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-jira/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - Jira
title: Jira integration for Grafana OnCall
weight: 500
---

# Jira integration for Grafana OnCall

The Jira integration for Grafana OnCall handles issue events sent from Jira webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

## Configure Jira integration for Grafana OnCall

You must have an Admin role to create integrations in Grafana OnCall.

1. In the **Integrations** tab, click **+ New integration to receive alerts**.
2. Select **Jira** from the list of available integrations.
3. Follow the instructions in the **How to connect** window to get your unique integration URL and review next steps.

## Grouping, auto-acknowledge and auto-resolve

Grafana OnCall provides grouping, auto-acknowledge and auto-resolve logic for the Jira integration:

- Alerts created from issue events are grouped by issue key
- Alert groups are auto-acknowledged when the issue status is set to "work in progress"
- Alerts are auto-resolved when the issue is closed or deleted

To customize this behaviour, consider modifying alert templates in integration settings.
