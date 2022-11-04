---
aliases:
  - ../integrations/configure-outgoing-webhooks/
  - /docs/oncall/latest/alert-behavior/outgoing-webhooks/
canonical: https://grafana.com/docs/oncall/latest/alert-behavior/outgoing-webhooks/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - amixr
  - webhooks
title: Configure outgoing webhooks for Grafana OnCall
weight: 500
---

# Configure outgoing webhooks for Grafana OnCall

Outgoing webhooks allow you to send alert details to a specified URL from Grafana OnCall. Once an outgoing webhook is configured, you can use it as a notification method in escalation chains.

To automatically send alert data to a destination URL via outgoing webhook:

1. In Grafana OnCall, navigate to **Outgoing Webhooks** and click **+ Create**.
   This is also the place to edit and delete existing outgoing webhooks.

2. Provide a name for your outgoing webhook and enter the destination URL.

3. If the destination requires authentication, enter your credentials.
   You can enter a username and password (HTTP) or an authorization header formatted in JSON.

4. Configure the webhook payload in the **Data** field.
5. Click **Create Webhook**.

The format you use to call the variables must match the structure of how the fields are nested in the alert payload. The **Data** field can use the following four variables to auto-populate the webhook payload with information about the first alert in the alert group:

- `{{ alert_payload }}`
- `{{ alert_group_id }}`
  <br>

`alert_payload` is always the first level of any variable you want to call.

The following is an example of an entry in the **Data** field that might return an alert name and description.

    ```json
    {
    "name": "{{ alert_payload.labels.alertname }}",
    "message": "{{ alert_payload.annotations.description }}"
    }
    ```

> **NOTE:** If you receive an error message and cannot create an outgoing webhook, verify that your JSON is formatted correctly.
