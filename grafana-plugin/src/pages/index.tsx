import React from 'react';

import { AppRootProps } from '@grafana/data';

import { config } from '@grafana/runtime';
import { useNavModel } from 'utils/hooks';
import { Switch, Route } from 'react-router-dom';

export const PLUGIN_URL_PATH = '/a/grafana-oncall-app';

export type PageDefinition = {
  path: string;
  icon: string;
  id: string;
  text: string;
  hideFromTabs?: boolean;
  role?: 'Viewer' | 'Editor' | 'Admin';
};

function getPath(name = '') {
  return `${PLUGIN_URL_PATH}/${name}`;
}

export const pages: PageDefinition[] = [
  {
    icon: 'bell',
    id: 'incidents',
    text: 'Alert Groups',
    path: getPath('incidents'),
  },
  {
    icon: 'bell',
    id: 'incident',
    text: 'Incident',
    hideFromTabs: true,
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
    id: 'schedules-new',
    text: 'Schedules α',
    path: getPath('schedules-alfa'),
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
    text: 'Settings',
    path: getPath('settings'),
  },
  {
    icon: 'table',
    id: 'live-settings',
    text: 'Env Variables',
    role: 'Admin',
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
    icon: 'import',
    id: 'migration-tool',
    text: 'Migrate From Amixr.IO',
    hideFromTabs: true,
    path: getPath('migration-tool'),
  },
  {
    icon: 'cloud',
    id: 'cloud',
    text: 'Cloud',
    role: 'Admin',
    path: getPath('cloud'),
  },
  {
    icon: 'cog',
    id: 'test',
    text: 'Test',
    hideFromTabs: true,
    path: getPath('test'),
  },
];
