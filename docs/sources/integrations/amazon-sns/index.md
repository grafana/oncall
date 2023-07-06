---
aliases:
  - add-amazon-sns/
  - /docs/oncall/latest/integrations/available-integrations/configure-amazon-sns/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-amazon-sns/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - amazon-sns
title: Amazon SNS
weight: 500
---

# Amazon SNS integration for Grafana OnCall

The Amazon SNS integration for Grafana OnCall handles ticket events sent from Amazon SNS webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin][user-and-team-management] to be able to create integrations
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

<!-- markdownlint-disable MD033 -->
{{% docs/reference %}}
[user-and-team-management]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
[user-and-team-management]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/user-and-team-management"
{{% /docs/reference %}}
<!-- markdownlint-enable MD033 -->
