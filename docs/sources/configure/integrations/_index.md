---
title: Grafana OnCall integrations
menuTitle: Integrations
description: An introduction to Grafana OnCall integrations.
weight: 100
keywords:
  - OnCall
  - Integrations
  - Alerts
  - Webhook integration
  - Notifications
canonical: https://grafana.com/docs/oncall/latest/configure/integrations/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/
  - /docs/grafana-cloud/alerting-and-irm/oncall/integrations/
  - ../integrations/ # /docs/oncall/<ONCALL_VERSION>/configure/integrations/
---

# Grafana OnCall integrations

An integration serves as the primary entry point for alerts that are processed by Grafana OnCall.
Integrations receive alerts through a unique API URL, interpret them using a set of templates tailored for the specific monitoring system, and initiate
escalations as necessary.

For more information about how to configure an integration, refer to [Configure and manage integrations](https://grafana.com/docs/oncall/latest/configure/integrations/integration-management/).

## Understand the integration alert flow

- An alert is received on an integration’s **Unique URL** as an HTTP POST request with a JSON payload (or via [Inbound email][inbound-email] for email integrations).

- The incoming alert is routed according to the [Routing Template][routing-template].

- Alerts are grouped based on the [Grouping ID Template][group-id-templates] and rendered using [Appearance Templates][appearance-templates].

- The alert group can be published to messaging platforms, based on the **Publish to Chatops** configuration.

- The alert group is escalated to users according to the Escalation Chains selected for the route.

- An alert group can be acknowledged or resolved with status updates based on its [Behavioral Templates][behavioral-templates].

- Users can perform actions listed in the [Alert Workflow][alert-workflow] section.

## Explore available integrations

Refer to [Integration references][integration-references] for a list of available integrations and specific set up instructions.

{{% docs/reference %}}
[appearance-templates]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating#appearance-templates"
[Appearance templates]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating#appearance-templates"

[behavioral-templates]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating#behavioral-templates"
[Behavioral templates]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating#behavioral-templates"

[group-id-templates]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating#grouping-id-template"
[Behavioral templates]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating#grouping-id-template"

[inbound-email]: "/docs/oncall -> /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/inbound-email"
[Inbound email]: "/docs/grafana-cloud -> /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/inbound-email"

[jinja2-templating]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating"
[Jinja2 templating]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating"

[alert-workflow]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/set-up/get-started#learn-about-the-alert-workflow"
[Learn about the Alert Workflow]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/set-up/get-started#learn-about-the-alert-workflow"

[routing-template]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating#routing-template"
[Routing template]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating#routing-template"

[Webhooks]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/integrations/outgoing-webhooks"
[Webhooks]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/outgoing-webhooks"

[integration-labels]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/integrations/labels"
[integration-labels]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/labels"

[intergration-references]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/integrations/references"
[integration-references]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references"
{{% /docs/reference %}}
