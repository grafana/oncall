import { OrgRole } from '@grafana/data';
import { config } from '@grafana/runtime';
import { contextSrv } from 'grafana/app/core/core';

const ONCALL_PERMISSION_PREFIX = 'grafana-oncall-app';

export type UserAction = {
  permission: string;
  fallbackMinimumRoleRequired: OrgRole;
};

export enum Resource {
  ALERT_GROUPS = 'alert-groups',
  INTEGRATIONS = 'integrations',
  ESCALATION_CHAINS = 'escalation-chains',
  SCHEDULES = 'schedules',
  CHATOPS = 'chatops',
  OUTGOING_WEBHOOKS = 'outgoing-webhooks',
  MAINTENANCE = 'maintenance',
  API_KEYS = 'api-keys',
  NOTIFICATIONS = 'notifications',

  NOTIFICATION_SETTINGS = 'notification-settings',
  USER_SETTINGS = 'user-settings',
  OTHER_SETTINGS = 'other-settings',

  TEAMS = 'teams',
}

export enum Action {
  READ = 'read',
  WRITE = 'write',
  ADMIN = 'admin',
  TEST = 'test',
  EXPORT = 'export',
  UPDATE_SETTINGS = 'update-settings',
}

type Actions =
  | 'AlertGroupsRead'
  | 'AlertGroupsWrite'
  | 'IntegrationsRead'
  | 'IntegrationsWrite'
  | 'IntegrationsTest'
  | 'EscalationChainsRead'
  | 'EscalationChainsWrite'
  | 'SchedulesRead'
  | 'SchedulesWrite'
  | 'SchedulesExport'
  | 'ChatOpsRead'
  | 'ChatOpsWrite'
  | 'ChatOpsUpdateSettings'
  | 'OutgoingWebhooksRead'
  | 'OutgoingWebhooksWrite'
  | 'MaintenanceRead'
  | 'MaintenanceWrite'
  | 'APIKeysRead'
  | 'APIKeysWrite'
  | 'NotificationsRead'
  | 'NotificationSettingsRead'
  | 'NotificationSettingsWrite'
  | 'UserSettingsRead'
  | 'UserSettingsWrite'
  | 'UserSettingsAdmin'
  | 'OtherSettingsRead'
  | 'OtherSettingsWrite'
  | 'TeamsWrite';

const roleMapping: Record<OrgRole, number> = {
  [OrgRole.Admin]: 0,
  [OrgRole.Editor]: 1,
  [OrgRole.Viewer]: 2,
};

/**
 * The logic here is:
 * - an Admin should be able to do everything (including whatever an Editor and Viewer can do)
 * - an Editor should be able to do things Editors and Viewers can do
 * - a Viewer is only allowed to do things Viewers can do
 */
export const userHasMinimumRequiredRole = (minimumRoleRequired: OrgRole): boolean =>
  roleMapping[contextSrv.user.orgRole] <= roleMapping[minimumRoleRequired];

/**
 * See here for more info on the hasAccess method
 * https://github.com/grafana/grafana/blob/main/public/app/core/services/context_srv.ts#L165-L170
 *
 * As a fallback (second argument), for cases where RBAC is not enabled for a grafana instance, rely on basic roles
 */
export const isUserActionAllowed = ({ permission, fallbackMinimumRoleRequired }: UserAction): boolean =>
  config.featureToggles.accessControlOnCall
    ? !!contextSrv.user.permissions?.[permission]
    : userHasMinimumRequiredRole(fallbackMinimumRoleRequired);

/**
 * Given a `UserAction`, returns the permission or fallback-role, prefixed with "permission" or "role" respectively
 * depending on whether or not RBAC is enabled/disabled
 */
export const determineRequiredAuthString = ({ permission, fallbackMinimumRoleRequired }: UserAction): string =>
  config.featureToggles.accessControlOnCall ? `${permission} permission` : `${fallbackMinimumRoleRequired} role`;

/**
 * Can be used to generate a user-friendly message about which permission is missing. Method is RBAC-aware
 * and shows user the missing permission/basic-role depending on whether or not RBAC is enabled/disabled
 */
export const generateMissingPermissionMessage = (permission: UserAction): string =>
  `You are missing the ${determineRequiredAuthString(permission)}`;

export const generatePermissionString = (resource: Resource, action: Action, includePrefix: boolean): string =>
  `${includePrefix ? `${ONCALL_PERMISSION_PREFIX}.` : ''}${resource}:${action}`;

const constructAction = (
  resource: Resource,
  action: Action,
  fallbackMinimumRoleRequired: OrgRole,
  includePrefix = true
): UserAction => ({
  permission: generatePermissionString(resource, action, includePrefix),
  fallbackMinimumRoleRequired,
});

export const UserActions: { [action in Actions]: UserAction } = {
  AlertGroupsRead: constructAction(Resource.ALERT_GROUPS, Action.READ, OrgRole.Viewer),
  AlertGroupsWrite: constructAction(Resource.ALERT_GROUPS, Action.WRITE, OrgRole.Editor),

  IntegrationsRead: constructAction(Resource.INTEGRATIONS, Action.READ, OrgRole.Viewer),
  IntegrationsWrite: constructAction(Resource.INTEGRATIONS, Action.WRITE, OrgRole.Admin),
  IntegrationsTest: constructAction(Resource.INTEGRATIONS, Action.TEST, OrgRole.Editor),

  EscalationChainsRead: constructAction(Resource.ESCALATION_CHAINS, Action.READ, OrgRole.Viewer),
  EscalationChainsWrite: constructAction(Resource.ESCALATION_CHAINS, Action.WRITE, OrgRole.Admin),

  SchedulesRead: constructAction(Resource.SCHEDULES, Action.READ, OrgRole.Viewer),
  SchedulesWrite: constructAction(Resource.SCHEDULES, Action.WRITE, OrgRole.Editor),
  SchedulesExport: constructAction(Resource.SCHEDULES, Action.WRITE, OrgRole.Editor),

  ChatOpsRead: constructAction(Resource.CHATOPS, Action.READ, OrgRole.Viewer),
  ChatOpsWrite: constructAction(Resource.CHATOPS, Action.WRITE, OrgRole.Editor),
  ChatOpsUpdateSettings: constructAction(Resource.CHATOPS, Action.UPDATE_SETTINGS, OrgRole.Admin),

  OutgoingWebhooksRead: constructAction(Resource.OUTGOING_WEBHOOKS, Action.READ, OrgRole.Viewer),
  OutgoingWebhooksWrite: constructAction(Resource.OUTGOING_WEBHOOKS, Action.WRITE, OrgRole.Admin),

  MaintenanceRead: constructAction(Resource.MAINTENANCE, Action.READ, OrgRole.Viewer),
  MaintenanceWrite: constructAction(Resource.MAINTENANCE, Action.WRITE, OrgRole.Editor),

  APIKeysRead: constructAction(Resource.API_KEYS, Action.READ, OrgRole.Admin),
  APIKeysWrite: constructAction(Resource.API_KEYS, Action.WRITE, OrgRole.Admin),

  NotificationsRead: constructAction(Resource.NOTIFICATIONS, Action.READ, OrgRole.Editor),

  NotificationSettingsRead: constructAction(Resource.NOTIFICATION_SETTINGS, Action.READ, OrgRole.Viewer),
  NotificationSettingsWrite: constructAction(Resource.NOTIFICATION_SETTINGS, Action.WRITE, OrgRole.Editor),

  UserSettingsRead: constructAction(Resource.USER_SETTINGS, Action.READ, OrgRole.Viewer),
  UserSettingsWrite: constructAction(Resource.USER_SETTINGS, Action.WRITE, OrgRole.Editor),
  UserSettingsAdmin: constructAction(Resource.USER_SETTINGS, Action.ADMIN, OrgRole.Admin),

  OtherSettingsRead: constructAction(Resource.OTHER_SETTINGS, Action.READ, OrgRole.Viewer),
  OtherSettingsWrite: constructAction(Resource.OTHER_SETTINGS, Action.WRITE, OrgRole.Admin),

  // These are not oncall specific
  TeamsWrite: constructAction(Resource.TEAMS, Action.WRITE, OrgRole.Admin, false),
};
