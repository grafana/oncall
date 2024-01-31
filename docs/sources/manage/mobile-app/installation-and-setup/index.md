---
title: Installation and setup
menuTitle: Installation
description: Learn how to install and set up the Grafana OnCall mobile app.
weight: 100
keywords:
  - OnCall
  - Mobile app
  - iOS
  - Android
  - Push notification
canonical: https://grafana.com/docs/oncall/latest/manage/mobile-app/installation-and-setup/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/manage/mobile-app/installation-and-setup/
  - /docs/grafana-cloud/alerting-and-irm/oncall/mobile-app/installation-and-setup/
---

# Installation and setup

The Grafana OnCall mobile app is an extension of your Grafana OnCall instance.
Grafana OnCall is available for Grafana Cloud and Grafana open source users.
You must have a Grafana OnCall account to use this application.

## Installation of the Grafana Oncall Mobile app

Mobile app download:

- [Google Play Store](https://play.google.com/store/apps/details?id=com.grafana.oncall.prod)
- [Apple App Store](https://apps.apple.com/us/app/grafana-oncall-preview/id1669759048)

## Connect your Grafana OnCall account

The OnCall mobile app uses a QR code authentication to connect to your Grafana OnCall instance.
You can associate one Grafana OnCall user with your OnCall mobile app.

To connect your account in the mobile app:

1. Open the Grafana OnCall mobile app and tap **Sign in**
2. Follow the instructions in the app to complete QR code authentication
3. Once the scan is successful, your mobile app is connected to OnCall

<img src="/static/img/oncall/mobile-app-first-screen.png" width="300px">
<img src="/static/img/oncall/mobile-app-sign-in.png" width="300px">

### Where can I find my QR code?

To access your QR code:

1. Open Grafana OnCall from your desktop
1. Navigate to the **Users** tab, then tap **View my profile**
1. tap **Mobile app connection** in your profile

> **Note**: The QR code will timeout for security purposes - Screenshots of the QR code are unlikely to work for authentication.

### Connect to your open source Grafana OnCall account

Grafana OnCall OSS relies on Grafana Cloud OnCall as on relay for push notifications.
You must first connect your Grafana OnCall OSS to Grafana Cloud OnCall for the mobile app to work.

To connect to Grafana Cloud OnCall, refer to the Cloud page in your OSS Grafana OnCall instance.

For Grafana OnCall OSS, the QR code includes an authentication token along with a backend URL.
Your Grafana OnCall OSS instance should be reachable from the same network as your mobile device, preferably from the internet.
