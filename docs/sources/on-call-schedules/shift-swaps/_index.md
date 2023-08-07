---
title: Shift swap requests
canonical: https://grafana.com/docs/oncall/latest/on-call-schedules/shift-swaps/
description: "Learn more about Grafana OnCall shift swap requests"
keywords:
  - Grafana
  - oncall
  - schedule
  - swap
title: Shift swap requests
weight: 400
---

# Shift swap requests

A shift swap request allows users to seek volunteers among their teammates to cover their on-call shifts
in a schedule for a specified time span.

## Make a swap request

To request a shift swap, you can use the OnCall mobile app or the web UI in a schedule details page.

In the app, clicking on one of your shifts will show you an option to setup a swap request for that
event. You can customize other parameters from there too.

It is also possible to setup a request from a schedule view, tapping on the `request a swap` button.
You will need to specify a starting and ending datetimes and an optional description that will be
displayed when notifying other users about the request.

[screenshot swap request button / config screen]

In the web UI, you can follow a similar flow via the `Request shift swap` button, available in the `Rotations` lane
of a schedule, or clicking the button shown when hovering on a particular shift event in which you are on-call.

[screenshot swap request button / config screen]

>**Note**: no recurrence rules support is available when requesting a shift swap. If you need to recurrently change a shift,
consider creating a higher level layer rotation with the desired updates.

Upon submitting the request, a Slack notification will be sent to the channel associated to the correspondent
schedule, if there is one. Besides, people participating in the schedule may receive a [mobile push notification][shift-swap-notifications]
with the details.

[screenshot slack/mobile notification]

You can delete the swap request at any time. If the swap has been taken, it will automatically be undone upon removal.

## Check existing swap requests

To review existing swap requests, check the events identified with the swap request icon in a schedule view,
in the mobile app or in the web UI.

[screenshot swap pending]

[screenshot swap details]

## Take a swap request

If you are not the request owner and the request is still open, you have the option to take the swap. By doing so,
you will replace the requester in the given schedule for their respective shifts during the specified period.

If no one takes the swap request before its starting datetime, the request will be closed, and the original user
will remain on-call if there is a shift at that time.

Before taking a swap, you can review the involved shifts times.

[screenshot swap review]

Once a swap is taken, the affected rotations and the final schedule will reflect the changes.

[screenshot swap taken]

{{% docs/reference %}}
[shift-swap-notifications]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/mobile-app/push-notifications#shift-swap-notifications"
[shift-swap-notifications]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/mobile-app/push-notifications#shift-swap-notifications"
{{% /docs/reference %}}
