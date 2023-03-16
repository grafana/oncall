---
aliases:
  - /docs/oncall/latest/configure-user-settings/
canonical: https://grafana.com/docs/oncall/latest/configure-user-setting/
keywords:
  - Grafana Cloud
  - Permission
  - Notifications
  - RBAC
  - amixr
  - oncall
title: Manage users and teams for Grafana OnCall
weight: 1300
---

# Manage users and teams for Grafana OnCall

Grafana OnCall relies on the teams and user permissions configured at the organization level of your Grafana instance. Organization administrators can invite
users, configure teams, and manage user permissions at [Grafana.com](https://grafana.com/auth/sign-in).

## User roles and permissions

>**Note:** User roles and teams cannot be managed directly from Grafana OnCall.

User roles and permissions are assigned and managed at the Grafana organization or Cloud portal level. There are two ways to manage user roles and permissions
for Grafana OnCall:

1. Basic role authorization
  
By default, authorization within Grafana OnCall relies on the basic user roles configured at the organization level. All users are assigned a basic role by the
organization administrator. There are three available roles: `Viewer`, `Editor`, and `Admin`.

1. Role-based access control (RBAC)

RBAC for Grafana plugins allows for fine-grained access control so you can define custom roles and actions for users in Grafana OnCall. Use RBAC to grant
specific permissions within the Grafana OnCall plugin without changing the user’s basic role at the organization level. You can fine-tune basic roles to add or
remove certain Grafana OnCall RBAC roles.

For example, a user with the basic `Viewer` role at the organization level needs to edit on-call schedules. You can assign the Grafana OnCall RBAC role of
`Schedules Editor` to allow the user to view everything in Grafana OnCall, as well as allow them to edit on-call schedules.

To learn more about RBAC for Grafana OnCall, refer to the following documentation:

- [Manage RBAC roles](https://grafana.com/docs/grafana/latest/administration/roles-and-permissions/access-control/manage-rbac-roles/#update-basic-role-permissions)
- [RBAC permissions, actions, and scopes](https://grafana.com/docs/grafana/latest/administration/roles-and-permissions/access-control/custom-role-actions-scopes/)

## Manage Teams in Grafana OnCall

Teams in Grafana OnCall are based on the teams created at the organization level of your Grafana instance,
in **Configuration > Teams**. Administrators can create a different configuration for each team, and can navigate
between team configurations in the **Select Team** dropdown menu in the **Alert Group** section of Grafana OnCall.

Users, including admins, can only view and manage teams in OnCall if they are a member of that team.
An admin user may need to temporarily add themselves to a team to manage it.

## Configure user notification policies

Notification policies are a configurable set of notification steps that determine how you're notified of alert in OnCall. Users with the Admin or Editor role are
able to receive notifications.
Users can verify phone numbers and email addresses in the **Users** tab of Grafana OnCall.

- **Default Notifications** dictate how a user is notified for most escalation thresholds.

- **Important Notifications** are labeled in escalation chains. If an escalation event is marked as an important notification,
it will bypass **Default Notification** settings and notify the user by the method specified.

> **NOTE**: You cannot add users or manage permissions in Grafana OnCall. User settings are found on the
> organizational level of your Grafana instance in **Configuration > Users**.

To configure a users notification policy:

1. Navigate to the **Users** tab of Grafana OnCall and search for or select a user.

1. Click **Edit** to the right of a user to open the **User Info** window.

1. Verify that there is a valid and verified phone number, along with ChatOps accounts in order to receive notifications via those methods.

1. Click **Add notification step** and use the dropdowns to specify the notification method and frequency. Notification steps will be followed in the order they
are listed.

## Configure Telegram user settings in OnCall

1. In your profile, navigate to Telegram setting and click **Connect**.
1. Click **Connect automatically** for the bot to message you and to bring up your telegram account.
1. Click **Start** when the OnCall bot messages you.

To connect manually, you can click the URL provided and then **SEND MESSAGE**. In your Telegram account,
click **Start**.

## Configure Slack user settings in OnCall

1. In your profile, find the Slack setting and click **Connect**.
1. Follow the instructions to verify your account.
