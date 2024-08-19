---
title: Grafana Alerting integration for Grafana OnCall
menuTitle: Grafana Alerting
description: Grafana Alerting integration reference material for Grafana OnCall.
weight: 0
keywords:
  - OnCall
  - Integrations
  - Alerts
  - Grafana Alerting
  - Notifications
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/references/grafana-alerting
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/grafana-alerting
  - /docs/grafana-cloud/alerting-and-irm/oncall/integrations/grafana-alerting
  - add-grafana-alerting/
  - ../integrations/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/grafana-alerting
refs:
  trigger-webhook-template:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL VERSION>/configure/integrations/outgoing-webhooks/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/outgoing-webhooks/
  data-webhook-template:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL VERSION>/configure/integrations/outgoing-webhooks/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/outgoing-webhooks/
---

# Grafana Alerting integration for Grafana OnCall

{{< admonition type="note" >}}

⚠️ **Legacy** integration ⚠️
Integrations that were created before version 1.3.21 were marked as **(Legacy)** and recently migrated.
These integrations are receiving and escalating alerts, but some manual adjustments might be required.
{{< /admonition >}}

Grafana Alerting for Grafana OnCall can be set up using two methods:

- Grafana OnCall is connected to the same Grafana instance being used to manage Grafana OnCall.
- Grafana OnCall is connected to one or more Grafana instances, separate from the one being used to manage Grafana OnCall.

## Configure Grafana Alerting in same Grafana instance

Use the following method if you are connecting Grafana OnCall with alerts coming from the same Grafana instance from
which Grafana OnCall is being managed.

1. In Grafana OnCall, navigate to the **Integrations** tab and select **New Integration to receive alerts**.
1. Click **Quick connect** in the **Grafana Alerting** tile. This will open a **New Grafana Alerting integration** configuration window.

1. In the opened window, enter a name and description for the integration and choose existing or create a new contact point.
   This contact point will send alerts to the created integration.

   > **Note:** You must connect the contact point with a notification policy in Grafana Alerting to receive alerts in Grafana OnCall.
   > For more information, see
   > [Contact points in Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/unified-alerting/contact-points/)

1. Determine the escalation chain for the new integration by either selecting an existing one or by creating a new
   escalation chain.
1. In Grafana Cloud Alerting, navigate to **Alerting > Contact Points** and find a contact point with a name matching
   the integration you created in Grafana OnCall.
1. Click the **Edit** (pencil) icon, then click **Test**. This will send a test alert to Grafana OnCall.

## Configure external Grafana Alerting from other Grafana Instance

Connect Grafana OnCall with alerts coming from a Grafana instance that is different from the instance that Grafana
OnCall is being managed:

1. In Grafana OnCall, navigate to the **Integrations** tab and select **New Integration to receive alerts**.
1. Select the **Alertmanager** tile.
1. Enter a name and description for the integration, click Create
1. A new page will open with the integration details. Copy the OnCall Integration URL from HTTP Endpoint section.
1. Go to the other Grafana instance to connect to Grafana OnCall and navigate to **Alerting > Contact Points**.
1. Select **New Contact Point**.
1. Choose the contact point type `webhook`, then paste the URL generated in step 3 into the URL field.

   > **Note:** You must connect the contact point with a notification policy in Grafana Alerting to receive alerts in Grafana OnCall.
   > For more information, see
   > [Contact points in Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/unified-alerting/contact-points/)

1. Click the **Edit** (pencil) icon, then click **Test**. This will send a test alert to Grafana OnCall.

## Note about grouping and autoresolution

Grafana OnCall relies on the Grafana Alerting grouping and autoresolution mechanism to ensure consistency between alert state in OnCall and AlertManager.
It's recommended to configure [grouping](https://grafana.com/docs/grafana/latest/alerting/fundamentals/notification-policies/notifications/#grouping) on
the Grafana Alerting side and use default grouping and autoresolution templates on the OnCall side.
Changing this templates might lead to incorrect grouping and autoresolution behavior.

## Note about legacy integration

Before we were using each alert from Grafana Alerting group as a separate payload:

```json
{
  "labels": {
    "severity": "critical",
    "alertname": "InstanceDown"
  },
  "annotations": {
    "title": "Instance localhost:8081 down",
    "description": "Node has been down for more than 1 minute"
  },
  ...
}
```

This behaviour was leading to mismatch in alert state between OnCall and Grafana Alerting and draining of rate-limits,
since each Grafana Alerting alert was counted separately.

We decided to change this behaviour to respect Grafana Alerting grouping by using AlertManager group as one payload.

```json
{
  "alerts": [...],
  "groupLabels": {
    "alertname": "InstanceDown"
  },
  "commonLabels": {
    "job": "node", 
    "alertname": "InstanceDown"
  },
  "commonAnnotations": {
    "description": "Node has been down for more than 1 minute"
  },
  "groupKey": "{}:{alertname=\"InstanceDown\"}",
  ...
}
```

You can read more about AlertManager Data model [here](https://prometheus.io/docs/alerting/latest/notifications/#data).

### After-migration checklist

> Integration URL will stay the same, so no need to change AlertManager or Grafana Alerting configuration.
> Integration templates will be reset to suit new payload.
> It is needed to adjust routes and outgoing webhooks manually to new payload.

1. Send a new demo alert to the migrated integration.
2. Adjust routes to the new shape of payload. You can use payload of the demo alert from previous step as an example.
3. If outgoing webhooks utilized the alerts payload from the migrated integration in the [trigger](ref:trigger-webhook-template)
or [data](ref:data-webhook-template) template it's needed to adjust them as well.
