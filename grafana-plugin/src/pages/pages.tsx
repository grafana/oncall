import { NavModelItem } from '@grafana/data';
import { UserActions, UserAction, isUserActionAllowed } from 'helpers/authorization/authorization';
import { PLUGIN_ROOT } from 'helpers/consts';
import { matchPath } from 'react-router-dom-v5-compat';

import { AppFeature } from 'state/features';
import { RootBaseStore } from 'state/rootBaseStore/RootBaseStore';

export type PageDefinition = {
  path: string;
  icon: string;
  id: string;
  text: string;
  hideFromTabsFn?: (store: RootBaseStore) => boolean;
  hideFromTabs?: boolean;
  action?: UserAction;
  hideTitle: boolean; // dont't automatically render title above page content

  getPageNav: (pageTitle: string) => NavModelItem;
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
    icon: 'bell',
    id: 'alert-group',
    text: '',
    showOrgSwitcher: true,
    getParentItem: (pageTitle: string) => ({
      text: pageTitle,
      url: `${PLUGIN_ROOT}/alert-groups`,
    }),
    hideFromBreadcrumbs: true,
    hideFromTabs: true,
    path: getPath('alert-group/:id?'),
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
    hideTitle: true,
    hideFromBreadcrumbs: true,
    path: getPath('schedules'),
    action: UserActions.SchedulesRead,
  },
  {
    icon: 'calendar-alt',
    id: 'schedule',
    text: '',
    getParentItem: (pageTitle: string) => ({
      text: pageTitle,
      url: `${PLUGIN_ROOT}/schedules`,
    }),
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
    hideFromTabs: true,
    action: UserActions.ChatOpsRead,
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
      return !hasLiveSettings;
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
      return !hasCloudFeature;
    },
    path: getPath('cloud'),
    action: UserActions.OtherSettingsWrite,
  },
  {
    icon: 'cloud',
    id: 'insights',
    text: 'Insights',
    path: getPath('insights'),
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
      getPageNav: (pageTitle: string) =>
        ({
          text: '',
          parentItem: current.getParentItem ? current.getParentItem(pageTitle) : undefined,
          hideFromBreadcrumbs: current.hideFromBreadcrumbs,
          hideFromTabs: current.hideFromTabs,
        } as NavModelItem),
    };
  }

  return prev;
}, {});

export const ROUTES = {
  'alert-groups': ['alert-groups', 'alert-groups/:id'],
  users: ['users', 'users/:id'],
  integrations: ['integrations', 'integrations/:id'],
  escalations: ['escalations', 'escalations/:id'],
  schedules: ['schedules', 'schedules/:id'],
  outgoing_webhooks: ['outgoing_webhooks', 'outgoing_webhooks/:id', 'outgoing_webhooks/:action/:id'],
  settings: ['settings'],
  'chat-ops': ['chat-ops'],
  'live-settings': ['live-settings'],
  cloud: ['cloud'],
  insights: ['insights'],
  test: ['test'],

  // backwards compatible to redirect to new alert-groups
  incident: ['incidents/:id'],
  incidents: ['incidents'],
};

export function getMatchedPage(url: string) {
  return Object.keys(ROUTES).find((key) => {
    return ROUTES[key].find((route: string) => {
      const computedRoute = `${PLUGIN_ROOT}/${route}`;
      const isMatch = matchPath({ path: computedRoute, end: true }, url);
      return isMatch;
    });
  });
}
