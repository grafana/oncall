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
  - ../../mobile-app/installation-and-setup/ # /docs/oncall/<ONCALL_VERSION>/mobile-app/installation-and-setup/
---

# Installation and setup

The Grafana OnCall mobile app is an extension of your Grafana OnCall instance.
Grafana OnCall is available for Grafana Cloud and Grafana open source users.
You must have a Grafana OnCall account to use this application.

## Installation of the Grafana Oncall Mobile app

Mobile app download:

- [Google Play Store](https://play.google.com/store/apps/details?id=com.grafana.oncall.prod)
- [Apple App Store](https://apps.apple.com/us/app/grafana-oncall-preview/id1669759048)

## Connect your Grafana OnCall account using deeplink authentication

You can connect your Grafana OnCall account to the mobile app using a deeplink authentication.
This method is useful because it allows you to connect your account using only your mobile device.

To connect your account in the mobile app:

1. Open Grafana OnCall from your mobile device
2. Click on your profile icon in the top right corner
3. Click on the **IRM** tab
4. Click on the **Sign in** button

## Connect your Grafana OnCall account using QR code authentication

Another way to connect your Grafana OnCall account to the mobile app is by using a QR code authentication.

To connect your account in the mobile app:

1. Open the Grafana OnCall mobile app and tap **Sign in**
2. Follow the instructions in the app to complete QR code authentication
3. Once the scan is successful, your mobile app is connected to OnCall

<img src="/static/img/oncall/mobile-app-first-screen.png" width="300px">
<img src="/static/img/oncall/mobile-app-sign-in.png" width="300px">

### Where can I find my QR code?

To access your QR code:

1. Open Grafana OnCall from your desktop
2. Click on your profile icon in the top right corner
3. Click on the **IRM** tab

> **Note**: The QR code will timeout for security purposes - Screenshots of the QR code are unlikely to work for authentication.

### Connect to your open source Grafana OnCall account

Grafana OnCall OSS relies on Grafana Cloud OnCall as on relay for push notifications.
You must first connect your Grafana OnCall OSS to Grafana Cloud OnCall for the mobile app to work.

To connect to Grafana Cloud OnCall, refer to the Cloud page in your OSS Grafana OnCall instance.

For Grafana OnCall OSS, the QR code includes an authentication token along with a backend URL.
Your Grafana OnCall OSS instance should be reachable from the same network as your mobile device, preferably from the internet.

### Connect to multiple OnCall stacks

The OnCall mobile app provides a seamless experience for managing multiple OnCall stacks/accounts.

With just a few taps, you can add and switch between different stacks, ensuring you have access to all your alerts and schedules
without the need to log in and out repeatedly.
This feature is designed to support professionals managing multiple projects or working across different teams, enhancing efficiency and response times.

Simply navigate to the settings menu, select the account tile, tap on the + icon and scan the QR code of the stack you wish to connect.

To switch stack, just select the one you wish to visualize from the accounts page.

Stay organized and responsive by managing all your OnCall needs in one place.

<img src="/static/img/oncall/mobile-app-settings-account.png" width="300px">
<img src="/static/img/oncall/mobile-app-accounts-page.png" width="300px">
