---
aliases:
  - add-grafana-alerting/
canonical: https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-grafana-alerting/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - Prometheus
title: Grafana Alerting
weight: 100
---

# Grafana Alerting integration for Grafana OnCall

Grafana Alerting for Grafana OnCall can be set up using two methods:

- Grafana Alerting: Grafana OnCall is connected to the same Grafana instance being used to manage Grafana OnCall.
- Grafana (Other Grafana): Grafana OnCall is connected to one or more Grafana instances separate from the one being
  used to manage Grafana OnCall.

## Configure Grafana Alerting for Grafana OnCall

You must have an Admin role to create integrations in Grafana OnCall.

1. In the **Integrations** tab, click **+ New integration to receive alerts**.
2. Select **Grafana Alerting** by clicking the **Quick connect** button or select **Grafana (Other Grafana)** from
   the integrations list.
3. Follow the configuration steps that display in the **How to connect** window to retrieve your unique integration URL
   and complete any necessary configurations.

### Configure Grafana Cloud Alerting

Use the following method if you are connecting Grafana OnCall with alerts coming from the same Grafana instance from
which Grafana OnCall is being managed.

1. In Grafana OnCall, navigate to the **Integrations** tab and select **New Integration to receive alerts**.
1. Click **Quick connect** in the **Grafana Alerting** tile. This will automatically create the integration in Grafana
   OnCall as well as the required contact point in Alerting.

   > **Note:** You must connect the contact point with a notification policy. For more information, see
   > [Contact points in Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/unified-alerting/contact-points/)

1. Determine the escalation chain for the new integration by either selecting an existing one or by creating a new
   escalation chain.
1. In Grafana Cloud Alerting, navigate to **Alerting > Contact Points** and find a contact point with a name matching
   the integration you created in Grafana OnCall.
1. Click the **Edit** (pencil) icon, then click **Test**. This will send a test alert to Grafana OnCall.

### Configure Grafana (Other Grafana)

Connect Grafana OnCall with alerts coming from a Grafana instance that is different from the instance that Grafana
OnCall is being managed:

1. In Grafana OnCall, navigate to the **Integrations** tab and select **New Integration to receive alerts**.
2. Select the **Grafana (Other Grafana)** tile.
3. Follow the configuration steps that display in the **How to connect** window to retrieve your unique integration URL
   and complete any necessary configurations.
4. Determine the escalation chain for the new integration by either selecting an existing one or by creating a
   new escalation chain.
5. Go to the other Grafana instance to connect to Grafana OnCall and navigate to **Alerting > Contact Points**.
6. Select **New Contact Point**.
7. Choose the contact point type `webhook`, then paste the URL generated in step 3 into the URL field.

   > **Note:** You must connect the contact point with a notification policy. For more information,
   > see [Contact points in Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/unified-alerting/contact-points/).

8. Click the **Edit** (pencil) icon, then click **Test**. This will send a test alert to Grafana OnCall.
