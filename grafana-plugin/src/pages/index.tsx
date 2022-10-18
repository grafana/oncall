import React from 'react';

import { AppRootProps } from '@grafana/data';

import ChatOpsPage from 'pages/chat-ops/ChatOps';
import CloudPage from 'pages/cloud/CloudPage';
import EscalationsChainsPage from 'pages/escalation-chains/EscalationChains';
import IncidentPage from 'pages/incident/Incident';
import IncidentsPage from 'pages/incidents/Incidents';
import IntegrationsPage from 'pages/integrations/Integrations';
import LiveSettingsPage from 'pages/livesettings/LiveSettingsPage';
import MaintenancePage from 'pages/maintenance/Maintenance';
import MigrationTool from 'pages/migration-tool/MigrationTool';
import OrganizationLogPage from 'pages/organization-logs/OrganizationLog';
import OutgoingWebhooks from 'pages/outgoing_webhooks/OutgoingWebhooks';
import SchedulePage from 'pages/schedule/Schedule';
import SchedulesPage2 from 'pages/schedules/Schedules';
import SchedulesPage from 'pages/schedules_NEW/Schedules';
import SettingsPage from 'pages/settings/SettingsPage';
import Test from 'pages/test/Test';
import UsersPage from 'pages/users/Users';

import { config } from '@grafana/runtime';
import { useNavModel } from 'utils/hooks';
import { Switch, Route } from 'react-router-dom';

export const PLUGIN_URL_PATH = '/a/grafana-oncall-app';

export type PageDefinition = {
  component: React.ComponentType<AppRootProps>;
  path: string;
  icon: string;
  id: string;
  text: string;
  hideFromTabs?: boolean;
  role?: 'Viewer' | 'Editor' | 'Admin';
};

export function App(props: AppRootProps) {
  if (!config.featureToggles.topnav) {
    useNavModel(props as any);
  }

  return (
    <Switch>
      {pages.map((page) => (
        <Route exact path={page.path} component={page.component} />
      ))}
    </Switch>
  );
}

function getPath(name = '') {
  return `${PLUGIN_URL_PATH}/${name}`;
}

export const pages: PageDefinition[] = [
  {
    component: IncidentsPage,
    icon: 'bell',
    id: 'incidents',
    text: 'Alert Groups',
    path: getPath('incidents'),
  },
  {
    component: IncidentPage,
    icon: 'bell',
    id: 'incident',
    text: 'Incident',
    hideFromTabs: true,
    path: getPath('incident/:id?'),
  },
  {
    component: UsersPage,
    icon: 'users-alt',
    id: 'users',
    text: 'Users',
    path: getPath('users'),
  },
  {
    component: IntegrationsPage,
    icon: 'plug',
    id: 'integrations',
    text: 'Integrations',
    path: getPath('integrations'),
  },
  {
    component: EscalationsChainsPage,
    icon: 'list-ul',
    id: 'escalations',
    text: 'Escalation Chains',
    path: getPath('escalations'),
  },
  {
    component: SchedulesPage2,
    icon: 'calendar-alt',
    id: 'schedules',
    text: 'Schedules',
    path: getPath('schedules'),
  },
  {
    component: SchedulesPage,
    icon: 'calendar-alt',
    id: 'schedules-new',
    text: 'Schedules α',
    path: getPath('schedules-alfa'),
  },
  {
    component: SchedulePage,
    icon: 'calendar-alt',
    id: 'schedule',
    text: 'Schedule',
    hideFromTabs: true,
    path: getPath('schedule/:id?'),
  },
  {
    component: ChatOpsPage,
    icon: 'comments-alt',
    id: 'chat-ops',
    text: 'ChatOps',
    path: getPath('chat-ops'),
  },
  {
    component: OutgoingWebhooks,
    icon: 'link',
    id: 'outgoing_webhooks',
    text: 'Outgoing Webhooks',
    path: getPath('outgoing_webhooks'),
  },
  {
    component: MaintenancePage,
    icon: 'wrench',
    id: 'maintenance',
    text: 'Maintenance',
    path: getPath('maintenance'),
  },
  {
    component: SettingsPage,
    icon: 'cog',
    id: 'settings',
    text: 'Settings',
    path: getPath('settings'),
  },
  {
    component: LiveSettingsPage,
    icon: 'table',
    id: 'live-settings',
    text: 'Env Variables',
    role: 'Admin',
    path: getPath('live-settings'),
  },
  {
    component: OrganizationLogPage,
    icon: 'gf-logs',
    id: 'organization-logs',
    text: 'Org Logs',
    hideFromTabs: true,
    path: getPath('organization-logs'),
  },
  {
    component: MigrationTool,
    icon: 'import',
    id: 'migration-tool',
    text: 'Migrate From Amixr.IO',
    hideFromTabs: true,
    path: getPath('migration-tool'),
  },
  {
    component: CloudPage,
    icon: 'cloud',
    id: 'cloud',
    text: 'Cloud',
    role: 'Admin',
    path: getPath('cloud'),
  },
  {
    component: Test,
    icon: 'cog',
    id: 'test',
    text: 'Test',
    hideFromTabs: true,
    path: getPath('test'),
  },
];
