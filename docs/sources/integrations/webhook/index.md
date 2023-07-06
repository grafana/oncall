---
aliases:
  - ../add-webhook-integration/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-webhook/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - Alertmanager
  - Prometheus
title: Inbound Webhook
weight: 700
---

# Inbound Webhook integrations for Grafana OnCall

Grafana OnCall directly supports many integrations, those that aren’t currently listed in the Integrations menu can be
connected using the webhook integration and configured alert templates.

With the webhook integration, you can connect to any alert source that isn't listed in the **Create Integration** page.

There are two available formats, **Webhook** and **Formatted Webhook**.

- **Webhook** will pull all of the raw JSON payload and display it in the manner that it's received.
- **Formatted Webhook** can be used if the alert payload sent by your monitoring service is formatted in a way that
  OnCall recognizes.

  The following fields are recognized, but none are required:

  - `alert_uid`: a unique alert ID for grouping.
  - `title`: a title.
  - `image_url`: a URL for an image attached to alert.
  - `state`: either `ok` or `alerting`. Helpful for auto-resolving.
  - `link_to_upstream_details`: link back to your monitoring system.
  - `message`: alert details.

To configure a webhook integration:

1. In the **Integrations** tab, click **+ New integration to receive alerts**.
2. Select either **Webhook** or **Formatted Webhook** integration.
3. Follow the configuration steps in the **How to connect** section of the integration settings.
4. Use the unique webhook URL to complete any configuration in your monitoring service to send POST requests. Use any
   http client, e.g. curl to send POST requests with any payload.

For example:

```bash
curl -X POST \
https://a-prod-us-central-0.grafana.net/integrations/v1/formatted_webhook/m12xmIjOcgwH74UF8CN4dk0Dh/ \
-H 'Content-Type: Application/json' \
-d '{
    "alert_uid": "08d6891a-835c-e661-39fa-96b6a9e26552",
    "title": "The whole system is down",
    "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/ee/Grumpy_Cat_by_Gage_Skidmore.jpg",
    "state": "alerting",
    "link_to_upstream_details": "https://en.wikipedia.org/wiki/Downtime",
    "message": "Smth happened. Oh no!"
}'
```

To learn how to use custom alert templates for formatted webhooks, see
[Configure alerts templates][jinja2-templating].

{{% docs/reference %}}
[jinja2-templating]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/jinja2-templating"
[jinja2-templating]: "/docs/grafana-cloud/ -> /docs/oncall/<ONCALL VERSION>/jinja2-templating"
{{% /docs/reference %}}
