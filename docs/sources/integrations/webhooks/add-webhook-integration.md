+++
title = "Webhook integration"
keywords = ["Grafana Cloud", "Alerts", "Notifications", "on-call", "Alertmanager", "Prometheus"]
weight = 100
+++

# Integrate with your alert source using webhooks

Grafana OnCall directly supports integrations from many alert sources, but you can connect to any alert source that isn't listed in the **Create Integration** page by using webhooks.

1. In **Integrations**, click **+ New integration for receiving alerts**.
1. Select a webhook format. 
    There are two available formats. **Webhook** and **Formatted Webhook**.
    * **Webhook** will pull all of the raw JSON information and display it in the manner that it is received.
    * **Formatted Webhook** can be used if the body of the alerts sent by your monitoring service are formatted in a way that OnCall can read. The following fields are recognized, but none are required: 
        * `alert_uid`: a unique alert ID for grouping.
        * `title`: a title.
        * `image_url`: a URL for an image attached to alert.
        * `state`: either `ok` or `alerting`. Helpful for auto-resolving.
        * `link_to_upstream_details`: link back to your monitoring system.
        * `message`: alert details.

        To learn how to use custom alert templates for formatted webhooks, see [Configure custom alert templates]({{< relref "../create-custom-templates/" >}}).

1. Use the unique webhook URL for requests. For example:

    ```json
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
