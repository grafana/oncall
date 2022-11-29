import { NavModelItem } from '@grafana/data';

import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { AppFeature } from 'state/features';
import { RootBaseStore } from 'state/rootBaseStore';
import { UserActions, UserAction } from 'utils/authorization';

export const PLUGIN_URL_PATH = '/a/grafana-oncall-app';

export type PageDefinition = {
  path: string;
  icon: string;
  id: string;
  text: string;
  hideFromTabsFn?: (store: RootBaseStore) => boolean;
  hideFromTabs?: boolean;
  action?: UserAction;

  getPageNav(): { text: string; description: string };
};

function getPath(name = '') {
  return `${PLUGIN_URL_PATH}/?page=${name}`;
}

export const pages: { [id: string]: PageDefinition } = [
  {
    icon: 'bell',
    id: 'incidents',
    hideFromBreadcrumbs: true,
    text: 'Alert Groups',
    path: getPath('incidents'),
    action: UserActions.AlertGroupsRead,
  },
  {
    icon: 'bell',
    id: 'incident',
    text: '',
    hideFromTabs: true,
    hideFromBreadcrumbs: true,
    parentItem: { text: 'Incident' },
    path: getPath('incident/:id?'),
    action: UserActions.AlertGroupsRead,
  },
  {
    icon: 'users-alt',
    id: 'users',
    hideFromBreadcrumbs: true,
    text: 'Users',
    path: getPath('users'),
    action: UserActions.UserSettingsRead,
  },
  {
    icon: 'plug',
    id: 'integrations',
    path: getPath('integrations'),
    hideFromBreadcrumbs: true,
    text: 'Integrations',
    action: UserActions.IntegrationsRead,
  },
  {
    icon: 'list-ul',
    id: 'escalations',
    text: 'Escalation Chains',
    hideFromBreadcrumbs: true,
    path: getPath('escalations'),
    action: UserActions.EscalationChainsRead,
  },
  {
    icon: 'calendar-alt',
    id: 'schedules',
    text: 'Schedules',
    hideFromBreadcrumbs: true,
    path: getPath('schedules'),
    action: UserActions.SchedulesRead,
  },
  {
    icon: 'calendar-alt',
    id: 'schedule',
    text: '',
    parentItem: { text: 'Schedule' },
    hideFromBreadcrumbs: true,
    hideFromTabs: true,
    path: getPath('schedule/:id?'),
    action: UserActions.SchedulesRead,
  },
  {
    icon: 'comments-alt',
    id: 'chat-ops',
    text: 'ChatOps',
    path: getPath('chat-ops'),
    hideFromBreadcrumbs: true,
    hideFromTabs: isTopNavbar(),
    action: UserActions.ChatOpsRead,
  },
  {
    icon: 'link',
    id: 'outgoing_webhooks',
    text: 'Outgoing Webhooks',
    path: getPath('outgoing_webhooks'),
    hideFromBreadcrumbs: true,
    action: UserActions.OutgoingWebhooksRead,
  },
  {
    icon: 'wrench',
    id: 'maintenance',
    text: 'Maintenance',
    hideFromBreadcrumbs: true,
    path: getPath('maintenance'),
    action: UserActions.MaintenanceRead,
  },
  {
    icon: 'cog',
    id: 'settings',
    text: 'Settings',
    hideFromBreadcrumbs: true,
    path: getPath('settings'),
    action: UserActions.OtherSettingsRead,
  },
  {
    icon: 'table',
    id: 'live-settings',
    text: 'Env Variables',
    role: 'Admin',
    hideFromTabsFn: (store: RootBaseStore) => {
      const hasLiveSettings = store.hasFeature(AppFeature.LiveSettings);
      return isTopNavbar() || window.grafanaBootData.user.orgRole !== 'Admin' || !hasLiveSettings;
    },
    path: getPath('live-settings'),
    action: UserActions.OtherSettingsRead,
  },
  {
    icon: 'cloud',
    id: 'cloud',
    text: 'Cloud',
    role: 'Admin',
    hideFromTabsFn: (store: RootBaseStore) => {
      const hasCloudFeature = store.hasFeature(AppFeature.CloudConnection);
      return isTopNavbar() || window.grafanaBootData.user.orgRole !== 'Admin' || !hasCloudFeature;
    },
    path: getPath('cloud'),
    action: UserActions.OtherSettingsWrite,
  },
  {
    icon: 'gf-logs',
    id: 'organization-logs',
    text: 'Org Logs',
    hideFromTabs: true,
    path: getPath('organization-logs'),
  },
  {
    icon: 'cog',
    id: 'test',
    text: 'Test',
    hideFromTabs: true,
    path: getPath('test'),
  },
].reduce((prev, current) => {
  prev[current.id] = {
    ...current,
    getPageNav: () =>
      ({
        text: isTopNavbar() ? '' : current.text,
        parentItem: current.parentItem,
        hideFromBreadcrumbs: current.hideFromBreadcrumbs,
        hideFromTabs: current.hideFromTabs,
      } as NavModelItem),
  };

  return prev;
}, {});
