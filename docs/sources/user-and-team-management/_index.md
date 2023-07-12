---
title: User and team management
keywords:
  - oncall
  - RBAC
  - permissions
  - notification
weight: 1300
---

# Manage users and teams for Grafana OnCall

Grafana OnCall relies on the teams and user permissions configured at the organization level of your Grafana instance. Organization administrators can invite
users, configure teams, and manage user permissions at [Grafana.com](https://grafana.com/auth/sign-in).

## User roles and permissions

> **Note:** User roles and teams cannot be managed directly from Grafana OnCall.

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
