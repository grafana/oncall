---
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

Teams in Grafana OnCall enable the configuration of visibility and filtering of resources, such as alert groups,
integrations, escalation chains, and schedules. OnCall teams are automatically synced with
[Grafana teams](https://grafana.com/docs/grafana/latest/administration/team-management/) created at the organization
level of your Grafana instance. To modify global settings like team name or team members, navigate to
**Configuration > Teams**. For OnCall-specific team settings,
go to **Alerts & IRM > OnCall > Settings > Teams and Access Settings**.

This section displays a list of teams, allowing you to configure team visibility and access to team resources for all
Grafana users, or only admins and team members. You can also set a default team, which is a user-specific setting;
the default team will be pre-selected each time a user creates a new resource. The team list includes a `No team` tag,
signifying that the resource has no team and is accessible to everyone.

Admins can view the list of all teams, while editors and viewers can only see teams (and their resources)
they are members of or if the team setting "who can see the team name and access the team resources" is set to
"all users of Grafana".

> ⚠️ In the main Grafana teams section, users can set team-specific user permissions, such as Admin, Editor, or Viewer,
> but only for resources within that team. Currently, Grafana OnCall ignores this setting and uses global roles instead.

Teams help filter resources on their respective pages, improving organization. You can assign a resource to a team when
creating it. Alert groups created via the Integration API inherit the team from the integration.

Resources from different teams can be connected with one another. For instance, you can create an integration in one
team, set up multiple routes for the integration, and utilize escalation chains from other teams. Users, schedules,
and outgoing webhooks from other teams can also be included in the escalation chain. If a user only has access to the
first team and not others, they will be unable to view the resource, which will display as `🔒 Private resource`.
This feature enables the distribution of escalations across various teams.

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
