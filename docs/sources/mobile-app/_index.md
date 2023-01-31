---
title: Grafana OnCall mobile app
aliases:
  - /docs/oncall/latest/mobile-app/
keywords:
  - Mobile App
  - oncall
  - notification
  - push notification
weight: 1200
---

# Grafana OnCall Mobile App

>**Note**: This application is currently in beta

The Grafana OnCall mobile app allows teams to monitor and respond to critical system events from anywhere.
On-call engineers can reimagine incident response with real-time alerts, on-call notifications, and a growing feature set.

## About Grafana OnCall mobile app
Grafana OnCall for iOS and Android allows you to:

- Override Do Not Disturb on your device to ensure delivery of critical alerts
- View and troubleshoot alert details from your mobile device
- Receive push notifications according to your personal notification settings
- Login with a quick and secure QR code authorization

The OnCall mobile app allows users to receive push notifications as part of their notification policy.
Push notifications are one of the many notification options in Grafana OnCall.Regardless of your notification preferences, it’s recommended that you configure a diverse set of notification methods.

The current version of the mobile app includes limited functionality and serves primarily as a notification method. The mobile app is in development, and some features are not yet available.
Stay tuned, we're working on it!

## Before you begin

The Grafana OnCall mobile app is intended to be used as an extension of your Grafana OnCall instance.
Grafana OnCall is available for Grafana Cloud and Grafana open source users.

- You must have a Grafana OnCall account to use this application
- Download Grafana OnCall Mobile app

Mobile app download - [Google Play](https://play.google.com/apps/testing/com.grafana.oncall.prod) and [Apple App Store](link)


## Connect your Grafana OnCall account 

The OnCall mobile app uses a QR code authentication to connect to your Grafana OnCall instance.
You can associate one Grafana OnCall user with your OnCall mobile app.

To connect your account in the mobile app:
1. Open the Grafana OnCall mobile app
1. Click **Sign in** and enter your Grafana Cloud credentials
1. Follow the instructions in the app to locate your QR code
1. Use the mobile app to scan the QR code in your User profile
1. Once the scan is successful, your mobile app is connected


### Where can I find my QR code?

To access your QR code:
1. Open Grafana OnCall from your desktop
1. Navigate to the **Users** tab, then click **View my profile**
1. Click **Mobile app connection** in your profile

>**Note**: The QR code will timeout for security purposes - Screenshots of the QR code are unlikely to work for authentication.

### Connect to your open source Grafana OnCall account

Grafana OnCall OSS relies on Grafana Cloud as on relay for push notifications. You must first connect your Grafana OnCall OSS to Grafana Cloud for the mobile app to work.
To connect to Grafana Cloud, refer to the Cloud page in your OSS Grafana OnCall instance. 

For Grafana OnCall OSS, the QR code includes an authentication token along with a backend URL. Grafana OnCall's engine should be reachable from the same network as your mobile device, preferably from the internet.

## Mobile app push notifications

There are two push notification options for the mobile app:

- **Mobile push** - Sends a typical push notification to your mobile device according to your device and app notification settings. Intended for all types of alerts.
- **Mobile push important** - Sends a privileged push notification that can bypass Do Not Disturb on your device. Intended for critical alerts.Device-specific settings may impact the functionality of these notifications.

>**Note**: Android users may need to review their device settings to ensure the Grafana OnCall mobile app is authorized to bypass Do Not Disturb. In your device settings, allow the Android Critical Message Channel notification channel to Override Do Not Disturb.
### Add mobile app to notification preferences
To receive push notifications from the Grafana OnCall mobile app, you must add them to your notification policy steps. 

1. From Grafana OnCall, navigate to the **Users** tab and click **View my profile**
1. In your **User Info** tab, update your Default and Important notification policies to include Mobile push notifications.

For more information about Notification Policies, refer to [Manage users and teams for Grafana OnCall](../configure-user-settings/_index.md)
