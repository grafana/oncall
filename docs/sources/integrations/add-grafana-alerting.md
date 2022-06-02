+++
title = "Configure alert notifications with Grafana Alerting"
keywords = ["Grafana Cloud", "Alerts", "Notifications", "on-call", "Prometheus"]
aliases = ["/docs/grafana-cloud/oncall/integrations/add-grafana-alerting/"]
weight = 300
+++

# Connect Grafana Alerting to Grafana OnCall

You must have the Admin role assigned to connect to Grafana OnCall.

1. Navigate to the **Integrations** tab in Grafana OnCall.

1. Click on the Grafana logo.

1. Follow the instructions that display in the dialog box to find a unique integration URL in the monitoring configuration.

## Grafana installations

Grafana OnCall can be set up using two methods:

- Grafana Alerting: Grafana OnCall is connected to the same Grafana instance being used to manage Grafana OnCall.

- Grafana (External): Grafana OnCall is connected to one or more Grafana instances separate from the one being used to manage Grafana OnCall.

### Grafana Cloud Alerting
Use the following method if you are connecting Grafana OnCall with alerts coming from the same Grafana instance from which Grafana OnCall is being managed.

1. In Grafana OnCall, navigate to the **Integrations** tab and select **New Integration for receiving alerts**.

1. Click **Quick connect** in the **Grafana Alerting** tile. This will automatically create the integration in Grafana OnCall as well as the required contact point in Alerting. 

    >**Note:** You must connect the contact point with a notification policy. For more information, see [Contact points in Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/unified-alerting/contact-points/)

1. Determine the escalation chain for the new integration by either selecting an existing one or by creating a new chain. For more information on creating escalation chains, see: [Configure alert notifications with Grafana OnCall]({{< relref "../configure-notifications" >}})..

1. In Grafana Cloud Alerting, navigate to **Alerting > Contact Points** and find a contact point with a name matching the integration you created in Grafana OnCall.

1. Click the **Edit** (pencil) icon, then click **Test**. This will send an alert to Grafana OnCall.

### Grafana (External)

Connect Grafana OnCall with alerts coming from an instance of Grafana different from the one on which Grafana OnCall is being managed:
1. In Grafana OnCall, navigate to the **Integrations** tab and select **New Integration for receiving alerts**.

1. Select the **Grafana** tile.

1. View and save the URL needed to connect.

1. Determine the escalation chain for the new integration by either selecting an existing one or by creating a new chain. For more information on creating escalation chains, see: [Configure alert notifications with Grafana OnCall]({{< relref "../configure-notifications/" >}}).

1. Go to the other Grafana instance to connect to Grafana OnCall and navigate to **Alerting > Contact Points**.

1. Select **New Contact Point**.

1. Choose the contact point type `webhook`, then paste the URL generated in step 3 into the URL field.

    >**Note:** You must connect the contact point with a notification policy. For more information, see [Contact points in Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/unified-alerting/contact-points/).

1. Click the **Edit** (pencil) icon, then click **Test**. This will send an alert to Grafana OnCall.