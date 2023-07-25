---
aliases:
  - add-elastalert/
  - /docs/oncall/latest/integrations/available-integrations/configure-elastalert/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-elastalert/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - elastalert
title: ElastAlert
weight: 500
---

# ElastAlert integration for Grafana OnCall

The ElastAlert integration for Grafana OnCall handles ticket events sent from ElastAlert webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin][user-and-team-management] to be able to create integrations in Grafana OnCall.

## Configuring Grafana OnCall to Receive Alerts from ElastAlert

1. In the **Integrations** tab, click **+ New integration**.
2. Select **ElastAlert** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.

## Configuring ElastAlert to Send Alerts to Grafana OnCall

To send an alert from ElastAlert to a webhook, follow these steps:

> Refer to [ElastAlert http-post docs](https://elastalert.readthedocs.io/en/latest/ruletypes.html#http-post) for more details

1. Open your ElastAlert configuration file (e.g., `config.yaml`).
2. Locate the `alert` section.
3. Add the following configuration for the webhook alert:

  ```yaml
  alert: post
  http_post_url: "http://example.com/api"
  http_post_static_payload:
    title: abc123
  ```

  Replace `"abc123"` with a suitable name for your alert, and `"http://example.com/api"` with **OnCall Integration URL**.
4. Save the configuration file.

After configuring the webhook, ElastAlert will send alerts to the specified endpoint when triggered.
Make sure your webhook endpoint is configured to receive and process the incoming alerts.

## Grouping, auto-acknowledge and auto-resolve

Grafana OnCall provides grouping, auto-acknowledge and auto-resolve logic for the ElastAlert integration:

- Alerts created from ticket events are grouped by ticket ID
- Alert groups are auto-acknowledged when the ticket status is set to "Pending"
- Alert groups are auto-resolved when the ticket status is set to "Solved"

To customize this behaviour, consider modifying alert templates in integration settings.

### Configuring Elastalert to send heartbeats to Grafana OnCall Heartbeat

Add the following rule to ElastAlert

```yaml
    index: elastalert_status
    type: any
    alert: post
    http_post_url: {{ heartbeat_url }}
    realert:
        minutes: 1
    alert_text: elastalert is still running
    alert_text_type: alert_text_only
```

{{% docs/reference %}}
[user-and-team-management]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
[user-and-team-management]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/user-and-team-management"
{{% /docs/reference %}}
