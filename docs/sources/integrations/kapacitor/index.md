---
aliases:
  - add-kapacitor/
  - /docs/oncall/latest/integrations/available-integrations/configure-kapacitor/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-kapacitor/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - kapacitor
title: Kapacitor
weight: 500
---

# Kapacitor integration for Grafana OnCall

The Kapacitor integration for Grafana OnCall handles ticket events sent from Kapacitor webhooks.
The integration provides grouping, auto-acknowledge and auto-resolve logic via customizable alert templates.

> You must have the [role of Admin]({{< relref "user-and-team-management" >}}) to be able to create integrations in Grafana OnCall.

## Configuring Grafana OnCall to Receive Alerts from Kapacitor

1. In the **Integrations** tab, click **+ New integration**.
2. Select **Kapacitor** from the list of available integrations.
3. Enter a name and description for the integration, click **Create**
4. A new page will open with the integration details. Copy the **OnCall Integration URL** from **HTTP Endpoint** section.

## Configuring Kapacitor to Send Alerts to Grafana OnCall

To send an alert from Kapacitor, you can follow these steps:

1. Create a Kapacitor TICKscript or modify an existing one to define the conditions for triggering the alert.
  The TICKscript specifies the data source, data processing, and the alert rule. Here's an example of a simple TICKscript:

  ```tickscript
  stream
      |from()
          .measurement('measurement_name')
          .where(lambda: <condition>)
      |alert()
          .webhook('<webhook_url>')
  ```

  Replace `'measurement_name'` with the name of the measurement you want to monitor, `<condition>`
  with the condition that triggers the alert, and `'<webhook_url>'` with **OnCall Integration URL**
2. Save the TICKscript file with a `.tick` extension, for example, `alert_script.tick`.
3. Start the Kapacitor service using the TICKscript:

  ```bash
  kapacitor define <alert_name> -tick /path/to/alert_script.tick
  kapacitor enable <alert_name>
  kapacitor reload
  ```

  Replace `<alert_name>` with a suitable name for your alert.
4. Ensure that the Kapacitor service is running and actively monitoring the data.
When the condition defined in the TICKscript is met, Kapacitor will trigger the alert and send
a POST request to the specified webhook URL with the necessary information. Make sure your webhook
endpoint is configured to receive and process the incoming alerts from Kapacitor.
