import { NavModelItem } from '@grafana/data';
import { matchPath } from 'react-router-dom';

import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';
import { AppFeature } from 'state/features';
import { RootBaseStore } from 'state/rootBaseStore';
import { UserActions, UserAction, isUserActionAllowed } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';

export type PageDefinition = {
  path: string;
  icon: string;
  id: string;
  text: string;
  hideFromTabsFn?: (store: RootBaseStore) => boolean;
  hideFromTabs?: boolean;
  action?: UserAction;
  hideTitle: boolean; // dont't automatically render title above page content

  getPageNav(): { text: string; description: string };
};

function getPath(name = '') {
  return `${PLUGIN_ROOT}/${name}`;
}

export const pages: { [id: string]: PageDefinition } = [
  {
    icon: 'bell',
    id: 'alert-groups',
    hideFromBreadcrumbs: true,
    text: 'Alert groups',
    hideTitle: true,
    path: getPath('alert-groups'),
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
    text: 'Integrations',
    path: getPath('integrations'),
    hideTitle: true,
    hideFromBreadcrumbs: true,
    action: UserActions.IntegrationsRead,
  },
  {
    icon: 'list-ul',
    id: 'escalations',
    text: 'Escalation chains',
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
      url: `${PLUGIN_ROOT}/schedules`,
    },
    hideFromBreadcrumbs: true,
    hideFromTabs: true,
    path: getPath('schedule/:id?'),
    action: UserActions.SchedulesRead,
  },
  {
    icon: 'link',
    id: 'outgoing_webhooks',
    text: 'Outgoing webhooks',
    path: getPath('outgoing_webhooks'),
    hideFromBreadcrumbs: true,
    action: UserActions.OutgoingWebhooksRead,
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
    hideFromTabsFn: (store: RootBaseStore) => {
      const hasCloudFeature = store.hasFeature(AppFeature.CloudConnection);
      return isTopNavbar() || !hasCloudFeature;
    },
    path: getPath('cloud'),
    action: UserActions.OtherSettingsWrite,
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

export const ROUTES = {
  'alert-groups': ['alert-groups'],
  'alert-group': ['alert-groups/:id'],
  users: ['users', 'users/:id'],
  integrations: ['integrations'],
  integration: ['integrations/:id'],
  escalations: ['escalations', 'escalations/:id'],
  schedules: ['schedules'],
  schedule: ['schedules/:id'],
  outgoing_webhooks: ['outgoing_webhooks', 'outgoing_webhooks/:id', 'outgoing_webhooks/:action/:id'],
  maintenance: ['maintenance'],
  settings: ['settings'],
  'chat-ops': ['chat-ops'],
  'live-settings': ['live-settings'],
  cloud: ['cloud'],
  test: ['test'],

  // backwards compatible to redirect to new alert-groups
  incident: ['incidents/:id'],
  incidents: ['incidents'],
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
