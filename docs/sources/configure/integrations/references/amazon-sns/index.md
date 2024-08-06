---
title: Amazon SNS integration for Grafana OnCall
menuTitle: Amazon SNS
description: Amazon SNS integration reference material for Grafana OnCall.
weight: 0
keywords:
  - OnCall
  - Integrations
  - Alerts
  - Amazon SNS
  - Notifications
labels:
  products:
    - cloud
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/references/amazon-sns
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/amazon-sns
  - /docs/grafana-cloud/alerting-and-irm/oncall/integrations/amazon-sns
  - add-amazon-sns/
  - ../integrations/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/amazon-sns
refs:
  user-and-team-management:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/user-and-team-management/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/user-and-team-management/
---

# Amazon SNS integration for Grafana OnCall

> This integration is available in Cloud only.

The Amazon SNS integration for Grafana OnCall handles ticket events sent from Amazon SNS webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin](ref:user-and-team-management) to be able to create integrations
in Grafana OnCall.

## Configuring Grafana OnCall to Receive Alerts from Amazon SNS

1. In the **Integrations** tab, click **+ New integration**.
2. Select **Amazon SNS** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from
**HTTP Endpoint** section.

## Configuring Amazon SNS to Send Alerts to Grafana OnCall

1. Create a new Topic in <https://console.aws.amazon.com/sns>
2. Open this topic, then create a new subscription
3. Choose the protocol HTTPS
4. Add the **OnCall Integration URL** to the Amazon SNS Endpoint
