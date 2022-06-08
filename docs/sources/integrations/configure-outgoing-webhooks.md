+++
title = "Configure outgoing webhooks for Grafana OnCall"
keywords = ["Grafana Cloud", "Alerts", "Notifications", "on-call", "amixr", "webhooks"]
weight = 500
+++

# Configure outgoing webhooks for Grafana OnCall
You can configure outgoing webhooks to send alerts to destination. Once a webhook is created, you can choose the webhook as a notification method in escalation steps. 

1. In Grafana OnCall, navigate to **Outgoing Webhooks** and click **+ Create**.
    This is also the place to edit and delete existing webhooks.

1. Name your webhook and enter the destination URL.

1. If the destination requires authentication, enter your credentials.
    You can enter a username and password (HTTP) or an authorization header formatted in JSON.

1. Configure the webhook payload in the **Data** field. 
    You can use four variables to automate the body of your webhook. The format you use to call the variables must match the structure of how the fields are nested in your alert payload. The **Data** field can use the following four variables to auto-populate the webhook payload with information about the first alert in the alert group:
    - `{{ alert_title }}`
    - `{{ alert_message }}`
    - `{{ alert_url }}` 
    - `{{ alert_payload }}`
    <br>

    `alert_payload` is always the first level of any variable you want to call.

    The following is an example of an entry in the **Data** field that might return an alert name and description. 

    ```json
    {
    "name": "{{ alert_payload.labels.alertname }}",
    "message": "{{ alert_payload.annotations.description }}"
    }
    ```

    >**NOTE:** If you get an error message and cannot create a webhook, make sure your JSON is formatted correctly. 

1. Click **Create Webhook**.