---
canonical: https://grafana.com/docs/oncall/latest/mobile-app/push-notifications/
keywords:
  - Mobile App
  - oncall
  - notification
  - push notification
title: Push notifications
weight: 500
---

# Push notifications

There are three types of push notifications for the mobile app:

- **Mobile push** - Sends a typical push notification to your mobile device.  Intended for all types of alerts.
- **Mobile push important** - Sends a push notification for important alerts.  We recommend (and default) to louder notifications.
- **On-Call Shift Notifications** - Sends announcements for upcoming shifts (optional).

## Add mobile app to notification policies

To receive push notifications from the Grafana OnCall mobile app, you must add them to your notification policy steps.
**Important notifications** should include **Mobile push important** and **Default notifications** should include **Mobile push**.

In the **Settings** tab of the mobile app, tap on **Notification policies** to review, reorder, remove, add or change steps.  
Alternatively, you can do the same on desktop. From Grafana OnCall, navigate to the **Users** page, click **View my profile** and navigate to the **User Info** tab.

## Configuration

Use the **Push notifications** section in the **Settings** tab to configure push notifications.

### Android

On Android, we leverage the "Notification channels" system feature.
Each type of notification (**important**, **default**, and **on-call shifts**) registers a channel.
In this channel, you may configure the sound style, optional Do Not Disturb override, vibration, and so on.
**Customize notifications** takes you to this system menu, while hitting the **back** button or swiping left (if enabled) takes you back to the application.

**Volume Override** can optionally be configured in the mobile app itself.
Confusingly, this requires you to provide the **Override Do Not Disturb** permission to the application, in the system configuration.
The app will prompt for this if applicable.

>**Note**: You can explore included sounds and recommendations via the **Sound Library** button, but to change the sound, go to **Customize notifications**.

### iOS

On iOS, all configuration (such as sound selection, Do Not Disturb override, etc) happens inside the app.

For every type of notification (**important**, **default**, and **on-call shifts**), you can configure the sound and its style (constant vs intensifying).

You can also enable or disable Do Not Disturb override for **important** notifications.

### On-call shift notifications

On-call shift notifications are sent to announce upcoming shifts, roughly ~15 minutes in advance.

To enable or disable on-call shift notifications, use the **On-call shift notifications** section in the **Push notifications** settings.
