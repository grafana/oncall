---
aliases:
  - ../../notify/phone-sms
  - /docs/oncall/latest/notify/phone-sms/
canonical: https://grafana.com/docs/oncall/latest/notify/phone-sms/
keywords:
  - Grafana Cloud
  - Alerts
  - Notifications
  - on-call
  - amixr
  - oncall
  - slack
title: Phone calls and SMS
weight: 100
---

# Phone Calls and SMS notifications

Grafana OnCall Cloud includes SMS and Phone notifications, OSS users [could leverage][open-source] Grafana Cloud as a relay or
configure other providers like Twilio.

## Are there additional costs for outgoing calls/sms?

No, there are no additional costs for outgoing calls/sms.

## Are there rate-limits for calls/sms?

There are no specific limits, but we reserve the right to stop sending sms/calls in case of abnormal volume.

## Route incoming calls to the engineer who is on-call

Grafana OnCall does not provide a phone number for routing incoming requests. [GH Issue.](https://github.com/grafana/oncall/issues/1459)

## Is there a list of pre-defined phone numbers?

In order to learn the phone number used by OnCall, make a test call at the "Phone Verification" tab.

## Phone calls or SMS does not work for me

There are cases when OnCall is not able to make phone calls or send SMS to certain regions or specific phone numbers.
We're working hard to fix such cases, but kindly asking to test your personal notification chain to make sure OnCall
is able to notify you. Also we suggest to back up Phone Calls and SMS with other notification methods such as
[Mobile App][mobile-app].

{{% docs/reference %}}
[mobile-app]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/mobile-app"
[mobile-app]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/mobile-app"

[open-source]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/open-source"
[open-source]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/open-source"
{{% /docs/reference %}}
