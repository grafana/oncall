---
title: On-call schedules
aliases:
  - /docs/oncall/latest/on-call-schedules/
canonical: https://grafana.com/docs/oncall/latest/on-call-schedules/
description: "Learn more about on-call schedules"
keywords:
  - Grafana
  - oncall
  - on-call
  - schedule
  - calendar
weight: 700
---

## Before you begin

- Users with Admin or Editor roles can create, edit and delete schedules.
- Users with Viewer role cannot receive alert notifications, therefore, cannot be on-call.

For more information about permissions, refer to
[Manage users and teams for Grafana OnCall][user-and-team-management]

### Web-based schedule

Configure and manage on-call schedules directly in the Grafana OnCall plugin. Easily configure and preview rotations,
see teammates' time zones, and add overrides.

Learn more about [Web-based schedules][web-schedule]

### iCal import

Use any calendar service that uses the iCal format to manage and customize on-call schedules - Import rotations and
shifts from your calendar app to Grafana OnCall for widely accessible scheduling. iCal imports appear in Grafana
OnCall as read-only schedules but can be leveraged similarly to a web-based schedule.

Learn more about [iCal import schedules][ical-schedules]

### Terraform

Use the Grafana OnCall Terraform provider to manage schedules within your “as-code” workflow. Rotations configured
via Terraform are automatically added to your schedules in Grafana OnCall. Similar to the iCal import, these schedules
read-only and cannot be edited from the UI.

To learn more, read our [Get started with Grafana OnCall and Terraform](
<https://grafana.com/blog/2022/08/29/get-started-with-grafana-oncall-and-terraform/>) blog post.

{{% docs/reference %}}
[ical-schedules]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/on-call-schedules/ical-schedules"
[ical-schedules]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/on-call-schedules/ical-schedules"

[user-and-team-management]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/user-and-team-management"
[user-and-team-management]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/user-and-team-management"

[web-schedule]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/on-call-schedules/web-schedule"
[web-schedule]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/on-call-schedules/web-schedule"
{{% /docs/reference %}}

### Shift swap requests

Sometimes you may need someone to cover your scheduled on-call shifts (e.g. you are going on vacation
for a couple of weeks). You can then create a shift swap request, which will let your teammates
know about this as well as allowing them to volunteer and take your affected shifts for that period.

Learn more about [Shift swap requests][shift-swaps]
