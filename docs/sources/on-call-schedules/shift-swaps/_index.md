---
title: Shift swaps
canonical: https://grafana.com/docs/oncall/latest/on-call-schedules/shift-swaps/
description: "Learn more about Grafana OnCall shift swaps"
keywords:
  - Grafana
  - oncall
  - schedule
  - swap
title: Shift swaps
weight: 400
---

# Shift swaps

Shift swaps provide a convenient way for on-call engineers to find team members to exchange on-call shifts
in a schedule for a specified time span to covered planned or unplanned unavailability.

## Make a swap request

To request a shift swap, you can use the OnCall mobile app or the web UI in a schedule details page.

In the app, tapping one of your shifts presents an option to construct a shift swap request for that and/or
other shifts.

It is also possible to setup a request from a schedule view, tapping on the `request a swap`
button (<img src="/static/img/oncall/swap-mobile-button.png" width="25px">) displayed in the top-right corner.
Include shifts by tapping them and/or specify starting and ending datetimes (they don't need to match
shifts exactly). The optional description will be displayed when notifying other users about the request.

<img src="/static/img/oncall/swap-mobile-request.png" width="300px">

In the web UI, you can follow a similar flow via the `Request shift swap` button, available in the `Rotations` lane
of a schedule, or clicking the button shown when hovering on a particular shift event in which you are on-call.

<img src="/static/img/oncall/swap-web-hover.png">
<img src="/static/img/oncall/swap-web-request.png">

>**Note**: no recurrence rules support is available when requesting a shift swap. If you need to recurrently change a shift,
consider creating a higher level layer rotation with the desired updates.

Upon submitting the request, a Slack notification will be sent to the channel associated to the correspondent
schedule, if there is one. A [mobile push notification][shift-swap-notifications] will be sent to team members who
participate in the schedule and have the notifications enabled.

<img src="/static/img/oncall/swap-slack-notification.png">

As long as the request is open, there will be follow-up notifications posted to the same Slack channel
to remind about the request.
The follow-up notifications will be sent at the following intervals before the swap start:

- 4 weeks
- 3 weeks
- 2 weeks
- 1 week
- 3 days
- 2 days
- 1 day
- 12 hours

You can delete the swap request at any time. If the swap has been taken, it will automatically be undone upon removal.

>**Note**: if [RBAC][rbac] is enabled, a user is required to have the `SCHEDULES_WRITE` permission to create,
update, take or delete a swap request. `SCHEDULES_READ` will be enough to get details about existing requests.

## Check existing swap requests

To review existing swap requests, check the events identified with the swap request icon in a schedule view,
in the mobile app or in the web UI.

<img src="/static/img/oncall/swap-web-shift.png">

## Take a swap request

If you are not the request owner and the request is still open, you have the option to take the swap. By doing so,
you will replace the requester in the given schedule for their respective shifts during the specified period.

If no one takes the swap request before its starting datetime, the request will be closed, and the original user
will remain on-call if there is a shift at that time.

Before taking a swap, you can review the involved shifts times.

<img src="/static/img/oncall/swap-mobile-details.png" width="300px">

You can also check (and take) a swap request details in the web UI.

<img src="/static/img/oncall/swap-web-take.png">

Once a swap is taken, the affected rotations and the final schedule will reflect the changes.

{{% docs/reference %}}
[shift-swap-notifications]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/mobile-app/push-notifications#shift-swap-notifications"
[rbac]: "/docs/oncall/ -> /docs/oncall/latest/user-and-team-management/#role-based-access-control-rbac"
{{% /docs/reference %}}
