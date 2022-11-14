import { NavModelItem } from '@grafana/data';

import { isNewNavigation } from 'plugin/GrafanaPluginRootPage.helpers';

export const PLUGIN_URL_PATH = '/a/grafana-oncall-app';

export type PageDefinition = {
  path: string;
  icon: string;
  id: string;
  text: string;
  hideFromTabs?: boolean;
  role?: 'Viewer' | 'Editor' | 'Admin';

  getPageNav(): { text: string; description: string };
};

function getPath(name = '') {
  return `${PLUGIN_URL_PATH}/?page=${name}`;
}

export const pages: { [id: string]: PageDefinition } = [
  {
    icon: 'bell',
    id: 'incidents',
    text: 'Alert Groups',
    path: getPath('incidents'),
  },
  {
    icon: 'bell',
    id: 'incident',
    text: '',
    hideFromTabs: true,
    hideFromBreadcrumbs: true,
    parentItem: { text: 'Incident' },
    path: getPath('incident/:id?'),
  },
  {
    icon: 'users-alt',
    id: 'users',
    text: 'Users',
    path: getPath('users'),
  },
  {
    icon: 'plug',
    id: 'integrations',
    text: 'Integrations',
    path: getPath('integrations'),
  },
  {
    icon: 'list-ul',
    id: 'escalations',
    text: 'Escalation Chains',
    path: getPath('escalations'),
  },
  {
    icon: 'calendar-alt',
    id: 'schedules',
    text: 'Schedules',
    path: getPath('schedules'),
  },
  {
    icon: 'calendar-alt',
    id: 'schedule',
    text: 'Schedule',
    hideFromTabs: true,
    path: getPath('schedule/:id?'),
  },
  {
    icon: 'comments-alt',
    id: 'chat-ops',
    text: 'ChatOps',
    path: getPath('chat-ops'),
    hideFromTabs: isNewNavigation(),
  },
  {
    icon: 'link',
    id: 'outgoing_webhooks',
    text: 'Outgoing Webhooks',
    path: getPath('outgoing_webhooks'),
  },
  {
    icon: 'wrench',
    id: 'maintenance',
    text: 'Maintenance',
    path: getPath('maintenance'),
  },
  {
    icon: 'cog',
    id: 'settings',
    text: 'Organization Settings',
    path: getPath('settings'),
  },
  {
    icon: 'table',
    id: 'live-settings',
    text: 'Env Variables',
    role: 'Admin',
    hideFromTabs: isNewNavigation(),
    path: getPath('live-settings'),
  },
  {
    icon: 'gf-logs',
    id: 'organization-logs',
    text: 'Org Logs',
    hideFromTabs: true,
    path: getPath('organization-logs'),
  },
  {
    icon: 'cloud',
    id: 'cloud',
    text: 'Cloud',
    role: 'Admin',
    hideFromTabs: isNewNavigation(),
    path: getPath('cloud'),
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
        text: current.text,
        parentItem: current.parentItem,
        hideFromBreadcrumbs: current.hideFromBreadcrumbs,
        hideFromTabs: current.hideFromTabs,
      } as NavModelItem),
  };

  return prev;
}, {});
