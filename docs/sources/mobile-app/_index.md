---
title: Mobile App
aliases:
  - /docs/oncall/latest/mobile-app/
keywords:
  - Mobile App
  - oncall
  - notification
  - push notification
weight: 1100
---

# Grafana OnCall Mobile App

The Grafana OnCall mobile app allows teams to monitor and respond to critical system events from anywhere.
On-call engineers can start exploring the benefits of the Grafana OnCall mobile app, with real-time alerts, on-call notifications, and a growing feature set.

## About Grafana OnCall mobile app

The current version of the mobile app includes limited functionality and serves primarily as a notification method.
The mobile app is in development, and some features are not yet available.

Stay tuned, we're working on it!

Grafana OnCall mobile app key features:

- Override Do Not Disturb on your device to ensure delivery of critical alerts
- Receive push notifications according to your personal notification settings
- View alert details from your mobile device
- Login with a quick and secure QR code authorization

The OnCall mobile app allows users to receive push notifications as part of their notification policy.
Push notifications are one of the many notification options in Grafana OnCall.

Consider using multiple notification methods, such as mobile app and phone/SMS,
to remain available in case of degraded internet or phone network connectivity.

## Before you begin

The Grafana OnCall mobile app is intended to be used as an extension of your Grafana OnCall instance.
Grafana OnCall is available for Grafana Cloud and Grafana open source users.

- You must have a Grafana OnCall account to use this application
- Download Grafana OnCall mobile app

Mobile app download:

- [Google Play Store](https://play.google.com/store/apps/details?id=com.grafana.oncall.prod)
- [Apple App Store](https://apps.apple.com/us/app/grafana-oncall-preview/id1669759048)

## Connect your Grafana OnCall account

The OnCall mobile app uses a QR code authentication to connect to your Grafana OnCall instance.
You can associate one Grafana OnCall user with your OnCall mobile app.

To connect your account in the mobile app:

1. Open the Grafana OnCall mobile app and click **Sign in**
2. Follow the instructions in the app to complete QR code authentication
3. Once the scan is successful, your mobile app is connected to OnCall

### Where can I find my QR code?

To access your QR code:

1. Open Grafana OnCall from your desktop
1. Navigate to the **Users** tab, then click **View my profile**
1. Click **Mobile app connection** in your profile

>**Note**: The QR code will timeout for security purposes - Screenshots of the QR code are unlikely to work for authentication.

### Connect to your open source Grafana OnCall account

Grafana OnCall OSS relies on Grafana Cloud as on relay for push notifications.
You must first connect your Grafana OnCall OSS to Grafana Cloud for the mobile app to work.

To connect to Grafana Cloud, refer to the Cloud page in your OSS Grafana OnCall instance.

For Grafana OnCall OSS, the QR code includes an authentication token along with a backend URL.
Your Grafana OnCall OSS instance should be reachable from the same network as your mobile device, preferably from the internet.

## Mobile app push notifications

There are three types of push notifications for the mobile app:

- **Mobile push** - Sends a typical push notification to your mobile device.  Intended for all types of alerts.
- **Mobile push important** - Sends a push notification for important alerts.  We recommend (and default) to louder notifications.
- **On-Call Shift Notifications** - Sends announcements for upcoming shifts (optional).

### Add mobile app to notification policies

To receive push notifications from the Grafana OnCall mobile app, you must add them to your notification policy steps.
**Important notifications** should include **Mobile push important** and **Default notifications** should include **Mobile push**.

In the **Settings** tab of the mobile app, tap on **Notification policies** to review, reorder, remove, add or change steps.
Alternatively, you can do the same on desktop. From Grafana OnCall, navigate to the **Users** page, click **View my profile** and navigate to the **User Info** tab.

### Configuration

Use the **Push notifications** section in the **Settings** tab to configure push notifications.

#### Android

On Android, we leverage the "Notification channels" system feature. Each type of notification (**important**, **default**, and **on-call shifts**) registers a channel.
In this channel, you may configure the sound style, optional Do Not Disturb override, vibration, and so on.
- **Customize notifications** takes you to this system menu, while hitting the **back** button or swiping left (if enabled) takes you back to the application.
- **Volume Override** can optionally be configured in the mobile app itself. Confusingly, this requires you to provide the **Override Do Not Disturb** permission to the application, in the system configuration.  The app will prompt for this if applicable.

>**Note**: You can explore included sounds and recommendations via the **Sound Library** button, but to actually change the sound, you must go to **Customize notifications**.

#### iOS

On iOS, all configuration (such as sound selection, Do Not Disturb override, etc) happens inside the app.

For every type of notification (**important**, **default**, and **on-call shifts**), you can configure the sound and its style (constant vs intensifying).

You can also enable or disable Do Not Disturb override for **important** notifications.

#### On-call shift notifications

On-call shift notifications are sent to all users who are going to be on-call in the next ~15 minutes.

To enable or disable on-call shift notifications, use the **On-call shift notifications** section in the **Push notifications** settings.

## On-call status & shift information

On the **Feed** page, your avatar on top of the screen indicates whether you are oncall, will be on call soon, or not.  Tap on it to open the **upcoming shifts** view.  This view presents your current, and next upcoming shifts (if any), up to 1 month into the future.



