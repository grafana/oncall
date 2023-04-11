---
title: On-call schedules
aliases:
  - /docs/oncall/latest/calendar-schedules/
canonical: https://grafana.com/docs/oncall/latest/calendar-schedules/
description: "Learn more about on-call schedules"
keywords:
  - Grafana
  - oncall
  - schedule
  - calendar
weight: 1100
---

# On-call schedules

Grafana OnCall makes it easier to establish consistent and thoughtful on-call coverage while ensuring that alerts don’t
go unnoticed. Use Grafana OnCall to:

- Define coverage needs and avoid gaps in coverage
- Automate alert escalation
- Configure on-call shift notifications

This section provides conceptual information about Grafana OnCall schedule options.

## About on-call schedules

An on-call schedule consist of one or more rotations that contain on-call shifts. A schedule must be referenced in the
corresponding escalation chain for alert notifications to be sent to an on-call user.

A fully configured on-call schedule consists of three main components:

- **Rotations**: A recurring schedule containing a set of on-call shifts that users rotate through.
- **On-call shifts**: The period of time that an individual user is on-call for a particular rotation
- **Escalation Chains**: Automated steps that determine who to notify of an alert group.

## Types of on-call schedules

On-call schedules look different for different organizations and even teams. Grafana OnCall offers three different
options for managing your on-call schedules, so you can choose the option that best fits your needs.

### Web-based schedule

Configure and manage on-call schedules directly in the Grafana OnCall plugin. Easily configure and preview rotations,
see teammates' time zones, and add overrides.

Learn more about [Web-based schedules]({{< relref "web-schedule" >}})

### iCal import

Use any calendar service that uses the iCal format to manage and customize on-call schedules - Import rotations and
shifts from your calendar app to Grafana OnCall for widely accessible scheduling. iCal imports appear in Grafana
OnCall as read-only schedules but can be leveraged similarly to a web-based schedule.

Learn more about [iCal import schedules]({{< relref "ical-schedules" >}})

### Terraform

Use the Grafana OnCall Terraform provider to manage schedules within your “as-code” workflow. Rotations configured
via Terraform are automatically added to your schedules in Grafana OnCall. Similar to the iCal import, these schedules
read-only and cannot be edited from the UI.

To learn more, read our [Get started with Grafana OnCall and Terraform](
<https://grafana.com/blog/2022/08/29/get-started-with-grafana-oncall-and-terraform/>) blog post.
