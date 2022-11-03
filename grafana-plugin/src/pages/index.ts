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
import OrganizationLogPage2 from 'pages/organization-logs/OrganizationLog';
import OutgoingWebhooks2 from 'pages/outgoing_webhooks/OutgoingWebhooks';
import SchedulePage from 'pages/schedule/Schedule';
import SchedulesPage2 from 'pages/schedules/Schedules';
import SchedulesPage from 'pages/schedules_NEW/Schedules';
import SettingsPage2 from 'pages/settings/SettingsPage';
import Test from 'pages/test/Test';
import UsersPage2 from 'pages/users/Users';
import { UserActions, UserAction } from 'utils/authorization';

export type PageDefinition = {
  component: React.ComponentType<AppRootProps>;
  icon: string;
  id: string;
  text: string;
  hideFromTabs?: boolean;
  action?: UserAction;
};

export const pages: PageDefinition[] = [
  {
    component: IncidentsPage2,
    icon: 'bell',
    id: 'incidents',
    text: 'Alert Groups',
    action: UserActions.AlertGroupsRead,
  },
  {
    component: IncidentPage2,
    icon: 'bell',
    id: 'incident',
    text: 'Incident',
    hideFromTabs: true,
    action: UserActions.AlertGroupsRead,
  },
  {
    component: UsersPage2,
    icon: 'users-alt',
    id: 'users',
    text: 'Users',
    action: UserActions.UserSettingsRead,
  },
  {
    component: IntegrationsPage2,
    icon: 'plug',
    id: 'integrations',
    text: 'Integrations',
    action: UserActions.IntegrationsRead,
  },
  {
    component: EscalationsChainsPage,
    icon: 'list-ul',
    id: 'escalations',
    text: 'Escalation Chains',
    action: UserActions.EscalationChainsRead,
  },
  {
    component: SchedulesPage2,
    icon: 'calendar-alt',
    id: 'schedules',
    text: 'Schedules',
    action: UserActions.SchedulesRead,
  },
  {
    component: SchedulesPage,
    icon: 'calendar-alt',
    id: 'schedules-new',
    text: 'Schedules α',
    action: UserActions.SchedulesRead,
  },
  {
    component: SchedulePage,
    icon: 'calendar-alt',
    id: 'schedule',
    text: 'Schedule',
    hideFromTabs: true,
    action: UserActions.SchedulesRead,
  },
  {
    component: ChatOpsPage,
    icon: 'comments-alt',
    id: 'chat-ops',
    text: 'ChatOps',
    action: UserActions.ChatOpsRead,
  },
  {
    component: ChatOpsPage,
    icon: 'comments-alt',
    id: 'slack',
    text: 'ChatOps',
    hideFromTabs: true,
    action: UserActions.ChatOpsRead,
  },
  {
    component: OutgoingWebhooks2,
    icon: 'link',
    id: 'outgoing_webhooks',
    text: 'Outgoing Webhooks',
    action: UserActions.OutgoingWebhooksRead,
  },
  {
    component: MaintenancePage2,
    icon: 'wrench',
    id: 'maintenance',
    text: 'Maintenance',
    action: UserActions.MaintenanceRead,
  },
  {
    component: SettingsPage2,
    icon: 'cog',
    id: 'settings',
    text: 'Settings',
    action: UserActions.OtherSettingsRead,
  },
  {
    component: LiveSettingsPage,
    icon: 'table',
    id: 'live-settings',
    text: 'Env Variables',
    action: UserActions.OtherSettingsRead,
  },
  {
    component: CloudPage,
    icon: 'cloud',
    id: 'cloud',
    text: 'Cloud',
    action: UserActions.OtherSettingsWrite,
  },
  // TODO: should the following pages have any permissions associated with them?
  {
    component: OrganizationLogPage2,
    icon: 'gf-logs',
    id: 'organization-logs',
    text: 'Org Logs',
    hideFromTabs: true,
  },
  {
    component: Test,
    icon: 'cog',
    id: 'test',
    text: 'Test',
    hideFromTabs: true,
  },
];
