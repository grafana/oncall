---
aliases:
  - add-appdynamics/
  - /docs/oncall/latest/integrations/available-integrations/configure-appdynamics/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-appdynamics/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - AppDynamics
title: AppDynamics
weight: 500
---

# AppDynamics integration for Grafana OnCall

The AppDynamics integration for Grafana OnCall handles health rule violation events sent from AppDynamics actions.
The integration provides grouping and auto-resolve logic via customizable alert templates.

## Configure AppDynamics integration for Grafana OnCall

You must have an Admin role to create integrations in Grafana OnCall.

1. In the **Integrations** tab, click **+ New integration to receive alerts**.
2. Select **AppDynamics** from the list of available integrations.
3. Follow the instructions in the **How to connect** window to get your unique integration URL and review next steps.

## Grouping and auto-resolve

Grafana OnCall provides grouping and auto-resolve logic for the AppDynamics integration:

- Alerts created from health rule violation events are grouped by application and node name
- Alert groups are auto-resolved when the health rule violation is ended or canceled

To customize this behaviour, consider modifying alert templates in integration settings.
