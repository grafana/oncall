---
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/
  - /docs/oncall/ # /docs/oncall/<ONCALL_VERSION>/
canonical: https://grafana.com/docs/oncall/latest/
description: Learn about the key benefits and features of Grafana OnCall
labels:
  products:
    - cloud
    - oss
menuTitle: OnCall
title: Grafana OnCall
weight: 500
hero:
  title: Grafana OnCall
  level: 1
  image: /media/docs/grafana-cloud/alerting-and-irm/grafana-icon-oncall.svg
  width: 100
  height: 100
  description: Grafana OnCall allows you to automate alert routing and escalation to ensure swift resolution and service reliability.
cards:
  title_class: pt-0 lh-1
  items:
    - title: Introduction
      href: ./intro/
      description: Learn more about the key benefits and features that are available with Grafana OnCall.
      height: 24
    - title: Set up
      href: ./set-up/
      description: Explore the set up options for Grafana OnCall.
      height: 24
    - title: Configure
      href: ./configure/
      description: Customize alert escalation and routing with flexible configuration options. Explore how to configure alert templates, routing rules, and outgoing webhooks.
      height: 24
    - title: Integrations
      href: ./integrations/
      description: Connect external alert sources, ChatOps tools, and much more to ensure alerts and updates are routed to and from OnCall, regardless of the other tools in your workflow.
    - title: Manage on-call schedules
      href: ./manage/on-call-schedules/
      description: Create and manage on-call schedules, scheduled overrides, and shift swaps.
      height: 24
    - title: Configure user notifications
      href: ./manage/notify/
      description: Create, manage, and view user notification policies.
      height: 24
---

{{< docs/hero-simple key="hero" >}}

---

## Overview

Respond to issues faster and improve your service reliability with Grafana OnCall.
Integrated directly into Grafana Cloud, you can automatically route alerts to designated on-call teams and ChatOps
channels according to predefined escalation policies, schedules, and notification preferences.

Alleviate the burden of being on-call with customized schedules tailored to your team's availability and timezones.
Personalize notification settings to ensure individuals receive alerts through their preferred channels, such as SMS, mobile apps, or ChatOps platforms.

Through automated alert routing and escalation, Grafana OnCall reduces incident response time, minimizes downtime and helps mitigate the impact of incidents.

## Explore

{{< card-grid key="cards" type="simple" >}}
