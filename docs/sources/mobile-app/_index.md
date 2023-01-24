---
aliases:
  - /docs/oncall/latest/mobile-app/
keywords:
  - Mobile App
title: Mobile App
weight: 300
---

# Grafana OnCall Mobile App

Mobile app is one of the ways to receive notifications from Grafana OnCall. OnCall provides multiple ways of delivering notifications to give our users an option to use some of them as a backup. We suggest backing up your Slack, MS Teams, phone calls with notifications delivered to the mobile app or vise versa.

The current version of the app serves the only one purpose to act as a notification method. I's missing some features like a calendar editor or even a list of alert groups. This is a known limitation. Stay tuned, we're working on it!

Download Grafana OnCall Mobile app in Google Play and Apple App Store (links todo after publishing). 

## Connecting mobile app to the OnCall instance

Connecting mobile app to OnCall should be pretty straightforward. QR is used to transfer authentication token. The QR code has a pretty short timeout, so making screenshots to authenticate later won't work. One mobile application could be associated with one Grafana OnCall user.

**Open Source specific:**

OnCall OSS relies on Grafana Cloud as on relay for push notifications. Connecting Grafana OnCall Open Source to Grafana Cloud through OnCall -> Cloud is a requirement for mobile app to work.

QR code includes not only authentication token but also backend URL. Grafana OnCall's "engine" should be reachable from the same network as your mobile device (ideally from the internet).

## Routing alerts to the mobile app

Mobile notifacation's won't work until you add "Mobile push" and "Mobile push important" to your notification steps in your Notification Preferences (Grafana OnCall -> Users -> View My profile -> User Info).

"Mobile push" will generate typical push notification in your mobile device.

"Mobile push important" will generate previleged push notification. It should be able to bypass device's Do Not Disturb mode and designed for critical alerts only. Please test how exactly it works with your device before relying on it.