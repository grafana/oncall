+++
title = "Integrate with alert sources"
keywords = ["Grafana Cloud", "Alerts", "Notifications", "on-call", "Alertmanager", "Prometheus"]
aliases = ["/docs/grafana-cloud/oncall/integrations/add-integration/"]
weight = 100
+++

# Integrate with alert sources

Grafana OnCall can connect directly to the monitoring services of your alert sources listed in the Grafana OnCall **Integrations** section.

1. Connect to alert source with configured alerts.
    
    In Grafana OnCall, click on the **Integrations** tab and click **+ New integration for receiving alerts**.

1. Select an integration from the provided options.
    
    If you want to use an integration that is not listed, you must use webhooks. To learn more about using webhooks see [Integrate with webhooks]({{< relref "/integrations/webhooks/add-webhook-integration/" >}}).

1. Configure your integration.
    
    Each integration has a different method of connecting to Grafana OnCall. For example, if you want to connect to your Grafana as an alert source, select Grafana and follow the instructions. 
