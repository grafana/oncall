---
title: Grafana OnCall
menuTitle: OnCall
description: Learn about the key features of Grafana OnCall and how improve your IRM solution
weight: 500

# This is the oncall index document
# Please do not make changes to the weight of this document
# The weight is set for ordering in the docs/grafana-cloud/alerting-and-irm/ folder

keywords:
  - OnCall
  - Grafana Cloud
  - Alerts
  - Notifications
  - On-call
  - Escalation
  - IRM
canonical: https://grafana.com/docs/oncall/latest/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/
---

# Grafana OnCall documentation

Grafana OnCall is an incident response and on-call management system that helps teams reduce the stress and maintenance of being on-call. Based on the Grafana
OnCall OSS project, Grafana OnCall is available on Grafana Cloud as part of the Grafana Incident Response & Management (IRM) solution.

## What is Grafana OnCall?

Grafana OnCall is a robust on-call management and incident response tool that is conveniently integrated into your Grafana Cloud environment.

Positioned at the core of Grafana’s Incident Response & Management (IRM) solution, Grafana OnCall automatically routes and escalates alerts to on-call teams and
channels based on your predefined escalation policies and on-call schedules.

## Key features

### Diverse monitoring system support

Grafana OnCall integrates with a diverse set of monitoring systems, including Grafana, Prometheus, Alertmanager, Zabbix, and more. This flexibility ensures
that, regardless of your existing monitoring infrastructure, your team benefits from Grafana OnCall.

### Automatic escalation to on-call rotations

Efficiently manage on-call rotations using Grafana OnCall's flexible calendar options. Define on-call schedules directly in the OnCall app, in your preferred
calendar application with iCal format, or leverage Terraform within your "as-code" workflow. Configurable alert escalation routes notifications to on-call team
members, Slack channels, and other designated points, ensuring timely responses.

### ChatOps focused

Grafana OnCall integrates closely with your Slack workspace to deliver alert notifications to individuals and groups, making daily alerts more visible and
easier to manage.

### Mobile app

Access on-call alerts on the go with the dedicated mobile app, putting critical notifications in the palm of your hand.

### As-code and GitOps

Equipped with a full API and Terraform capabilities, Grafana OnCall is ready for GitOps and large organization configuration.

### Fully customizable

With customizable alert grouping and routing, you can decide which alerts you want to be notified of and how, ensuring the right people are notified for the
right issues.

## Common on-call challenges

Explore how Grafana OnCall addresses common on-call challenges:

- **Alert Noise and Fatigue:** Automatic grouping and configurable auto-resolve settings control alert noise and reduce fatigue during incidents.
- **Balancing On-Call Load:** Schedule balance feature identifies potential workload imbalances, ensuring fair distribution.
- **Tool Sprawl:** Grafana OnCall, part of the Grafana Cloud suite, centralizes alert responses and investigations.
- **Calendar Maintenance:** Manage on-call rotations efficiently with flexible calendar integration for easy scheduling and alert escalation.
- **Custom Workflows:** Tailor incident response workflows with highly customizable alert grouping and routing for targeted notifications.

## Get started

To learn more about what Grafana OnCall can do for you, explore the following topics:

{{< section >}}
