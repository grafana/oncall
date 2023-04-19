---
canonical: https://grafana.com/docs/oncall/latest/alert-behavior/
title: Configure alert behavior for Grafana OnCall
weight: 900
---

# Configure alert behavior for Grafana OnCall

The available alert configurations in Grafana OnCall allow you to define how certain alerts are handled and ensure that
alerts are routed, escalated, and grouped to fit your specific alerting needs. Grafana OnCall can receive alerts from
any monitoring system that sends alerts via webhook.

## About alert behavior

Once Grafana OnCall receives an alert, the following occurs, based on the alert content:

- Default or customized alert templates are applied to deliver the most useful alert fields with the most valuable information,
  in a readable format.
- Alerts are grouped based on your alert grouping configurations, combining similar or related alerts to reduce alert noise.
- Alerts automatically resolve if an alert from the monitoring system matches the resolve condition for that alert.

{{< section >}}
