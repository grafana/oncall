import React from 'react';

import { AppRootProps } from '@grafana/data';

import ChatOpsPage from 'pages/chat-ops/ChatOps';
import CloudPage from 'pages/cloud/CloudPage';
import EscalationsChainsPage from 'pages/escalation-chains/EscalationChains';
import IncidentPage2 from 'pages/incident/Incident';
import IncidentsPage2 from 'pages/incidents/Incidents';
import IntegrationsPage2 from 'pages/integrations/Integrations';
import LiveSettingsPage from 'pages/livesettings/LiveSettingsPage';
import MaintenancePage2 from 'pages/maintenance/Maintenance';
import MigrationTool from 'pages/migration-tool/MigrationTool';
import OrganizationLogPage2 from 'pages/organization-logs/OrganizationLog';
import OutgoingWebhooks2 from 'pages/outgoing_webhooks/OutgoingWebhooks';
import SchedulePage from 'pages/schedule/Schedule';
import SchedulesPage2 from 'pages/schedules/Schedules';
import SchedulesPage from 'pages/schedules_NEW/Schedules';
import SettingsPage2 from 'pages/settings/SettingsPage';
import Test from 'pages/test/Test';
import UsersPage2 from 'pages/users/Users';

export type PageDefinition = {
  component: React.ComponentType<AppRootProps>;
  icon: string;
  id: string;
  text: string;
  hideFromTabs?: boolean;
  role?: 'Viewer' | 'Editor' | 'Admin';
};

export const pages: PageDefinition[] = [
  {
    component: IncidentsPage2,
    icon: 'bell',
    id: 'incidents',
    text: 'Alert Groups',
  },
  {
    component: IncidentPage2,
    icon: 'bell',
    id: 'incident',
    text: 'Incident',
    hideFromTabs: true,
  },
  {
    component: UsersPage2,
    icon: 'users-alt',
    id: 'users',
    text: 'Users',
  },
  {
    component: IntegrationsPage2,
    icon: 'plug',
    id: 'integrations',
    text: 'Integrations',
  },
  {
    component: EscalationsChainsPage,
    icon: 'list-ul',
    id: 'escalations',
    text: 'Escalation Chains',
  },
  {
    component: SchedulesPage2,
    icon: 'calendar-alt',
    id: 'schedules',
    text: 'Schedules',
  },
  {
    component: SchedulesPage,
    icon: 'calendar-alt',
    id: 'schedules-new',
    text: 'Schedules α',
  },
  {
    component: SchedulePage,
    icon: 'calendar-alt',
    id: 'schedule',
    text: 'Schedule',
    hideFromTabs: true,
  },
  {
    component: ChatOpsPage,
    icon: 'comments-alt',
    id: 'chat-ops',
    text: 'ChatOps',
  },
  {
    component: ChatOpsPage,
    icon: 'comments-alt',
    id: 'slack',
    text: 'ChatOps',
    hideFromTabs: true,
  },
  {
    component: OutgoingWebhooks2,
    icon: 'link',
    id: 'outgoing_webhooks',
    text: 'Outgoing Webhooks',
  },
  {
    component: MaintenancePage2,
    icon: 'wrench',
    id: 'maintenance',
    text: 'Maintenance',
  },
  {
    component: SettingsPage2,
    icon: 'cog',
    id: 'settings',
    text: 'Settings',
  },
  {
    component: LiveSettingsPage,
    icon: 'table',
    id: 'live-settings',
    text: 'Env Variables',
    role: 'Admin',
  },
  {
    component: OrganizationLogPage2,
    icon: 'gf-logs',
    id: 'organization-logs',
    text: 'Org Logs',
    hideFromTabs: true,
  },
  {
    component: MigrationTool,
    icon: 'import',
    id: 'migration-tool',
    text: 'Migrate From Amixr.IO',
    hideFromTabs: true,
  },
  {
    component: CloudPage,
    icon: 'cloud',
    id: 'cloud',
    text: 'Cloud',
    role: 'Admin',
  },
  {
    component: Test,
    icon: 'cog',
    id: 'test',
    text: 'Test',
    hideFromTabs: true,
  },
];
