---
title: Webhook as personal notification channel
menuTitle: Webhook
description: Learn more about using webhooks as a personal notification channel in Grafana OnCall.
weight: 700
keywords:
  - OnCall
  - Notifications
  - ChatOps
  - Webhook
  - Channels
canonical: https://grafana.com/docs/oncall/latest/manage/notify/webhook/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/manage/notify/webhook/
  - /docs/grafana-cloud/alerting-and-irm/oncall/notify/webhook/
refs:
  outgoing-webhooks:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/integrations/outgoing-webhooks/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/outgoing-webhooks/
---

# Webhook as a personal notification channel

It is possible to setup a webhook as a personal notification channel in your user profile.
The webhook will be triggered as a personal notification rule according to your notification policy configuration.

## Configure a webhook to be used as personal notification

In the webhooks page, you (or a user with the right permissions) need to define a [webhook](ref:outgoing-webhooks) as usual,
but with the `Personal Notification` trigger type.

Each user will then be able to choose a webhook (between those with the above trigger type) as a notification channel in
their profile. Optionally, they can also provide additional context data (as a JSON dict, e.g. `{"user_ID": "some-id"}`)
which will be available when evaluating the webhook templates. This data can be referenced via `{{ event.user.<key> }}`
(e.g. `{{ event.user.user_ID }}`).
