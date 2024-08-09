---
title: On-call schedules
menuTitle: On-call schedules
description: Learn more about on-call schedules.
weight: 300
keywords:
  - On-call
  - Schedules
  - Rotation
  - Calendar
  - Shift
  - Scheduler
canonical: https://grafana.com/docs/oncall/latest/manage/on-call-schedules/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/manage/on-call-schedules/
  - /docs/grafana-cloud/alerting-and-irm/oncall/on-call-schedules/
  - ../on-call-schedules # /docs/oncall/<ONCALL_VERSION>/on-call-schedules/
refs:
  web-based-on-call-schedules:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/on-call-schedules/web-schedule/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/on-call-schedules/web-schedule/
  import-on-call-schedules:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/on-call-schedules/ical-schedules/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/on-call-schedules/ical-schedules/
  manage-users-and-teams-for-grafana-oncall:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/user-and-team-management/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/user-and-team-management/
  shift-swap-requests:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/on-call-schedules/shift-swaps/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/on-call-schedules/shift-swaps/
---

## Before you begin

- Users with Admin or Editor roles can create, edit and delete schedules.
- Users with Viewer role cannot receive alert notifications, therefore, cannot be on-call.

For more information about permissions, refer to [Manage users and teams for Grafana OnCall](ref:manage-users-and-teams-for-grafana-oncall)

### Web-based schedule

Configure and manage on-call schedules directly in the Grafana OnCall plugin. Easily configure and preview rotations,
see teammates' time zones, and add overrides.

For more information, refer to [Web-based on-call schedules](ref:web-based-on-call-schedules).

### iCal import

Use any calendar service that uses the iCal format to manage and customize on-call schedules - Import rotations and
shifts from your calendar app to Grafana OnCall for widely accessible scheduling. iCal imports appear in Grafana
OnCall as read-only schedules but can be leveraged similarly to a web-based schedule.

For more information, refer top [Import on-call schedules](ref:import-on-call-schedules).

### Terraform

Use the Grafana OnCall Terraform provider to manage schedules within your “as-code” workflow. Rotations configured
via Terraform are automatically added to your schedules in Grafana OnCall. Similar to the iCal import, these schedules
read-only and cannot be edited from the UI.

To learn more, read our [Get started with Grafana OnCall and Terraform](https://grafana.com/blog/2022/08/29/get-started-with-grafana-oncall-and-terraform/)
blog post.

### Shift swap requests

<div style="position: relative; padding-bottom: 56.25%; height: 0;">
  <iframe
    src="https://www.loom.com/embed/1638acd3033e48d5ace554e927a016a3?sid=ed08af31-5176-4c69-b91b-f76f4785eb0e"
    frameborder="0"
    webkitallowfullscreen
    mozallowfullscreen
    allowfullscreen
    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
  /></iframe>
</div>

Sometimes you may need someone to cover your scheduled on-call shifts (e.g. you are going on vacation
for a couple of weeks). You can then create a shift swap request, which will let your teammates
know about this as well as allowing them to volunteer and take your affected shifts for that period.

For more information, refer to [Shift swap requests](ref:shift-swap-requests).
