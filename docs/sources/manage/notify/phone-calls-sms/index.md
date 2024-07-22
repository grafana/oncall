---
title: Phone calls and SMS notifications
menuTitle: Phone and SMS
description: Learn more about Phone calls and SMS notifications for Grafana OnCall.
weight: 100
keywords:
  - OnCall
  - Notifications
  - SMS
  - Phone
  - Rate Limits
canonical: https://grafana.com/docs/oncall/latest/manage/notify/phone-calls-sms/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/manage/notify/phone-calls-sms/
  - /docs/grafana-cloud/alerting-and-irm/oncall/notify/phone-calls-sms/
  - ../../notify/phone-sms/ # /docs/oncall/<ONCALL_VERSION>/notify/phone-sms/
  - ../../notify/phone-calls-sms/ # /docs/oncall/<ONCALL_VERSION>/notify/phone-calls-sms/
---

# Phone calls and SMS notifications

Grafana OnCall Cloud includes SMS and Phone notifications, OSS users can use the [Grafana OSS-Cloud Setup][] as a relay or configure other providers like Twilio.

## Are there additional costs for outgoing calls/sms?

No, there are no additional costs for outgoing calls/sms.

## Are there rate-limits for calls/sms?

There are no specific limits, but we reserve the right to stop sending sms/calls in case of abnormal volume.

## Route incoming calls to the engineer who is on-call

See our [docs][Incoming Call Routing], and [blog post](https://grafana.com/blog/2024/06/10/a-guide-to-grafana-oncall-sms-and-call-routing/),
on Advanced SMS & call routing configuration, for a guide on how to configure incoming call routing.

## Is there a list of pre-defined phone numbers?

In order to learn the phone number used by OnCall, make a test call at the "Phone Verification" tab.

## Phone calls or SMS does not work for me

There are cases when OnCall is not able to make phone calls or send SMS to certain regions or specific phone numbers.
We're working hard to fix such cases, but kindly asking to test your personal notification chain to make sure OnCall
is able to notify you. Also we suggest to back up Phone Calls and SMS with other notification methods such as
[Mobile app][].

{{% docs/reference %}}
[Mobile app]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/manage/mobile-app"
[Mobile app]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/manage/mobile-app"

[Grafana OSS-Cloud Setup]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/set-up/open-source#grafana-oss-cloud-setup"
[Grafana OSS-Cloud Setup]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/set-up/open-source#grafana-oss-cloud-setup"

[Incoming Call Routing]: "/docs/oncall/ -> /docs/oncall/<ONCALL_VERSION>/configure/live-call-routing"
[Incoming Call Routing]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/configure/live-call-routing"
{{% /docs/reference %}}
