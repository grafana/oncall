---
aliases:
  - add-zendesk/
  - /docs/oncall/latest/integrations/available-integrations/configure-zendesk/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-zendesk/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - Zendesk
title: Zendesk
weight: 500
---

# Zendesk integration for Grafana OnCall

The Zendesk integration for Grafana OnCall handles ticket events sent from Zendesk webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

## Configure Zendesk integration for Grafana OnCall

You must have an Admin role to create integrations in Grafana OnCall.

1. In the **Integrations** tab, click **+ New integration to receive alerts**.
2. Select **Zendesk** from the list of available integrations.
3. Follow the instructions in the **How to connect** window to get your unique integration URL and review next steps.

## Grouping, auto-acknowledge and auto-resolve

Grafana OnCall provides grouping, auto-acknowledge and auto-resolve logic for the Zendesk integration:

- Alerts created from ticket events are grouped by ticket ID
- Alert groups are auto-acknowledged when the ticket status is set to "Pending"
- Alert groups are auto-resolved when the ticket status is set to "Solved"

To customize this behaviour, consider modifying alert templates in integration settings.
