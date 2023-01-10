import { NavModelItem } from '@grafana/data';
import { matchPath } from 'react-router-dom';

import { PLUGIN_ROOT } from 'plugin/GrafanaPluginRootPage';
import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { AppFeature } from 'state/features';
import { RootBaseStore } from 'state/rootBaseStore';
import { UserActions, UserAction, isUserActionAllowed } from 'utils/authorization';

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
    parentItem: {
      text: 'Incident',
      parentItem: {
        text: 'Incidents',
        url: `${PLUGIN_URL_PATH}/incidents`,
      },
    },
    path: getPath('users'),
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
    parentItem: {
      text: 'Schedule',
      parentItem: {
        text: 'Schedules',
        url: `${PLUGIN_URL_PATH}/schedules`,
      },
    },
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
      return isTopNavbar() || !hasLiveSettings;
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
      return isTopNavbar() || !hasCloudFeature;
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
  if (!current.action || (current.action && isUserActionAllowed(current.action))) {
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
  }

  return prev;
}, {});

const ROUTES = {
  incidents: ['incidents'],
  incident: ['incident/:id'],
  users: ['users', 'users/:id'],
  integrations: ['integrations', 'integrations/:id'],
  escalations: ['escalations', 'escalations/:id'],
  schedules: ['schedules'],
  schedule: ['schedules/:id'],
  outgoing_webhooks: ['outgoing_webhooks', 'outgoing_webhooks/:id'],
  maintenance: ['maintenance'],
  settings: ['settings'],
  'organization-logs': ['organization-logs'],
  test: ['test'],
};

export const getRoutesForPage = (name: string) => {
  return ROUTES[name].map((route) => `${PLUGIN_ROOT}/${route}`);
};

export function getMatchedPage(url: string) {
  return Object.keys(ROUTES).find((key) => {
    return ROUTES[key].find((route) =>
      matchPath(url, {
        path: `${PLUGIN_ROOT}/${route}`,
        exact: true,
        strict: false,
      })
    );
  });
}
