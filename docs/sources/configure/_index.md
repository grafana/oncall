---
title: Configure Grafana OnCall
menuTitle: Configure
description: Learn about the configuration option available for OnCall
weight: 400
keywords:
  - OnCall
  - Configuration
  - Integration
  - Escalation
  - Alert templates
  - Webhooks
canonical: https://grafana.com/docs/oncall/latest/configure/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/
refs:
  integrations:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/integrations/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/
  jinja2-templating:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/jinja2-templating/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/jinja2-templating/
  escalation-chains-and-routes:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/escalation-chains-and-routes/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/escalation-chains-and-routes/
---

# Configure Grafana OnCall

Grafana OnCall provides a unified platform for alert routing and on-call management. This section covers the high-level technical configuration options for
Grafana OnCall so you can tailor the system to your organization's specific needs.

## Key configuration

Explore key settings and integrations that allow you to customize your incident management process.

### Configure Integrations

Integrate with your tools and alert sources to begin routing alerts with Grafana OnCall.

For detailed information on configuring integrations, refer to the [Integrations](ref:integrations) documentation.

### Configure Escalation chains and routes

Escalation chains allow you to customize alert routing to align with your team's processes and workflows.
You have the flexibility to define how and when to escalate to different teams for different alerts.

For information on configuration options, refer to [Escalation chains and routes](ref:escalation-chains-and-routes).

### Customize alert templates

For detailed information on customizing alert templates, refer to the [Jinja2 templating](ref:jinja2-templating) documentation.
