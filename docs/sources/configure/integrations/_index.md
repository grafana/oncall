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
refs:
  integration-references:
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/
  group-id-templates:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating/#grouping-id-template
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating/#grouping-id-template
  intergration-references:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/
  appearance-templates:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating/#appearance-templates
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating/#appearance-templates
  inbound-email:
    - pattern: /docs/oncall
      destination: /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/inbound-email/
    - pattern: /docs/grafana-cloud
      destination: /docs/oncall/<ONCALL_VERSION>/configure/integrations/references/inbound-email/
  alert-workflow:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/set-up/get-started/#learn-about-the-alert-workflow
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/set-up/get-started/#learn-about-the-alert-workflow
  integration-labels:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/integrations/labels/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/labels/
  routing-template:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating/#routing-template
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating/#routing-template
  behavioral-templates:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating/#behavioral-templates
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating/#behavioral-templates
  webhooks:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/integrations/outgoing-webhooks/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/outgoing-webhooks/
  jinja2-templating:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating/
---

# Grafana OnCall integrations

An integration serves as the primary entry point for alerts that are processed by Grafana OnCall.
Integrations receive alerts through a unique API URL, interpret them using a set of templates tailored for the specific monitoring system, and initiate
escalations as necessary.

For more information about how to configure an integration, refer to [Configure and manage integrations](https://grafana.com/docs/oncall/latest/configure/integrations/integration-management/).

## Understand the integration alert flow

- An alert is received on an integration’s **Unique URL** as an HTTP POST request with a JSON payload (or via [Inbound email](ref:inbound-email) for email integrations).

- The incoming alert is routed according to the [Routing Template](ref:routing-template).

- Alerts are grouped based on the [Grouping ID Template](ref:group-id-templates) and rendered using [Appearance Templates](ref:appearance-templates).

- The alert group can be published to messaging platforms, based on the **Publish to Chatops** configuration.

- The alert group is escalated to users according to the Escalation Chains selected for the route.

- An alert group can be acknowledged or resolved with status updates based on its [Behavioral Templates](ref:behavioral-templates).

- Users can perform actions listed in the [Alert Workflow](ref:alert-workflow) section.

## Explore available integrations

Refer to [Integration references](ref:intergration-references) for a list of available integrations and specific set up instructions.
