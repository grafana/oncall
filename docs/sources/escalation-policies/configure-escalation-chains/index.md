---
canonical: https://grafana.com/docs/oncall/latest/escalation-policies/configure-escalation-chains/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - amixr
  - oncall
  - integrations
title: Configure and manage Escalation Chains
weight: 100
---

# Configure and manage Escalation Chains

Escalation policies dictate how users and groups are notified when an alert notification is created. They can be very
simple, or very complex. You can define as many escalation configurations for an integration as you need, and you can
send notifications for certain alerts to a designated place when certain conditions are met, or not met.

Escalation policies have three main parts:

- User settings, where a user sets up their preferred or required notification method.
- An **escalation chain**, which can have one or more steps that are followed in order when a notification is triggered.
- A **route**, that allows administrators to manage notifications by flagging expressions in an alert payload.

## Escalation chains

An escalation chain can have many steps, or only one step. For example, steps can be configured to notify multiple users
in some order, notify users that are scheduled for on-call shifts, ping groups in Slack, use outgoing webhooks to
integrate with other services, such as JIRA, and do a number of other automated notification tasks.

## Routes

An escalation workflow can employ **routes** that administrators can configure to filter alerts by regular expressions
in their payloads. Notifications for these alerts can be sent to individuals, or they can make use of a new
or existing escalation chain.
