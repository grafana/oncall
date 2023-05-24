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

Grafana OnCall Cloud includes SMS and Phone notifications, OSS users [could leverage]({{< relref "open-source" >}}) Grafana Cloud as a relay or
configure other providers like Twilio.

## Is there a list of pre-defined phone numbers?

In order to learn the phone number used by OnCall, make a test call at the "Phone Verification" tab.

## Phone calls or SMS does not work for me

There are cases when OnCall is not able to make phone calls or send SMS to certain regions or specific phone numbers.
We're working hard to fix such cases, but kindly asking to test your personal notification chain to make sure OnCall
is able to notify you. Also we suggest to back up Phone Calls and SMS with other notification methods such as
[Mobile App]({{< relref "mobile-app" >}}).
