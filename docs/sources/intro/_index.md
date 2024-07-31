---
title: Introduction to Grafana OnCall
menuTitle: Introduction
description: An introduction to Grafana OnCall including, an overview of key concepts and features, how it works, and what you can do with it.
weight: 100
keywords:
  - OnCall
  - Alert notifications
  - Escalation chains
  - On-call schedules
  - Grafana Cloud
  - on-call engineer
canonical: https://grafana.com/docs/oncall/latest/intro/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/intro/
refs:
  get-started:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/set-up/get-started/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/set-up/get-started/
---

# Introduction to Grafana OnCall

Grafana OnCall is the cornerstone of Grafana’s Incident Response & Management (IRM) solution. Designed with the on-call engineer in mind, Grafana OnCall enables
you to refine on-call operations, expedite issue resolution, and fortify the reliability of your observability stack.

## How it works

Grafana OnCall serves as the nerve center for your observability stack, ingesting, grouping, and routing alerts from anywhere in your systems. Configure rules
to dictate how alerts are routed and grouped, ensuring efficient incident management. With predefined escalation policies and on-call schedules, Grafana OnCall
automates the escalation process, delivering alerts to the right responder at the right time.

## Key terms and concepts

To navigate Grafana OnCall effectively, familiarize yourself with key terms and concepts:

- **Alert group:** Aggregated sets of related alerts that are grouped by some attribute.
- **Escalation chain:** A set of predefined steps, rules, and time intervals dictating how and when alerts are directed to OnCall schedules or users directly.
- **Routes:** Configurable paths that direct alerts to designated responders or channels. Tailor Routes to send alerts to specific escalation chains based on
alert details. Additionally, enhance flexibility by incorporating regular expressions when adding routes to integrations.
- **On-call schedule:** A calendar-based system defining when team members are on-call.
- **Rotation:** The scheduled shift during which a specific team or individual is responsible for incident response.
- **Shift:** The designated time period within a rotation when a team or individual is actively on-call.
- **Notification policy:** Set of rules dictating how, when, and where alerts notifications are sent to a responder.

## Next steps

To get started with Grafana OnCall, refer to [Get started](ref:get-started)

To learn more about what you can do with Grafana OnCall, visit the [Grafana Cloud IRM product page](https://grafana.com/products/cloud/irm/).
