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
refs:
  incoming-call-routing:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/live-call-routing/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/live-call-routing/
  mobile-app:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/mobile-app/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/mobile-app/
  grafana-oss-cloud-setup:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/set-up/open-source/#grafana-oss-cloud-setup
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/set-up/open-source/#grafana-oss-cloud-setup
---

# Phone calls and SMS notifications

Grafana OnCall Cloud includes SMS and Phone notifications.

{{< admonition type="note" >}}
OSS users can use the [Grafana OSS-Cloud Setup](ref:grafana-oss-cloud-setup) as a relay or configure this notification type using other providers like Twilio.
{{< /admonition >}}

## SMS notification behavior

OnCall reduces alert noise and distraction by bundling SMS notifications.
When multiple alert groups require notification within a short period, the first alert group triggers an immediate SMS.
A 2-minute "waiting period" follows, during which additional alerts are bundled. After this period, a single SMS with all alert information is sent.

Notifications are bundled based on their importance. Alerts from "default" and "important" notification policies are bundled separately.

### Example

If a user needs to be notified about 5 alert groups from 2 different integrations (3 from "Grafana Alerting" and 2 from "Health Check"),
they will receive an immediate notification for the first alert group and a bundled SMS for the remaining alerts after 2 minutes:

#### Example bundled notification

Grafana OnCall: Alert groups #101, #102, #103 and 1 more, from stack: TestOrg, integrations: GrafanaAlerting and 1 more.

## Route incoming calls to the on-call engineer

For guidance on configuring incoming call routing, refer to our [documentation](ref:incoming-call-routing), and [blog post](https://grafana.com/blog/2024/06/10/a-guide-to-grafana-oncall-sms-and-call-routing/)

## About phone call and SMS notifications

Please note the following about phone calls and SMS notifications:

### Additional costs for outgoing calls/SMS

There are no additional costs for outgoing calls or SMS notifications.

### Rate limits for Calls/SMS

There are no specific rate limits, but we reserve the right to stop sending SMS/calls in case of abnormal volume.

### Grafana OnCall phone numbers

To learn the phone number used by OnCall, make a test call from the “Phone Verification” tab.

### Phone calls or SMS not working

There are instances where OnCall may not be able to make phone calls or send SMS to certain regions or specific phone numbers. We are working to resolve these issues.
Please test your personal notification chain to ensure OnCall can notify you.
We also suggest backing up phone calls and SMS with other notification methods such as the [Mobile app](ref:mobile-app).
