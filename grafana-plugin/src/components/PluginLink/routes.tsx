import { AppRootProps } from '@grafana/data';

import { PageDefinition } from 'pages';
import ChatOpsPage from 'pages/chat-ops/ChatOps';
import CloudPage from 'pages/cloud/CloudPage';
import EscalationsChainsPage from 'pages/escalation-chains/EscalationChains';
import IncidentPage from 'pages/incident/Incident';
import IncidentsPage from 'pages/incidents/Incidents';
import IntegrationsPage from 'pages/integrations/Integrations';
import LiveSettingsPage from 'pages/livesettings/LiveSettingsPage';
import MaintenancePage from 'pages/maintenance/Maintenance';
import OrganizationLogPage from 'pages/organization-logs/OrganizationLog';
import OutgoingWebhooks from 'pages/outgoing_webhooks/OutgoingWebhooks';
import SchedulePage from 'pages/schedule/Schedule';
import SchedulesPage2 from 'pages/schedules/Schedules';
import SchedulesPage from 'pages/schedules_NEW/Schedules';
import SettingsPage from 'pages/settings/SettingsPage';
import Test from 'pages/test/Test';
import UsersPage from 'pages/users/Users';

export interface NavMenuItem {
  meta: AppRootProps['meta'];
  pages: { [id: string]: PageDefinition };
  path: string;
  page: string;
  grafanaUser: {
    orgRole: 'Viewer' | 'Editor' | 'Admin';
  };
  enableLiveSettings: boolean;
  enableCloudPage: boolean;
  enableNewSchedulesPage: boolean;
  backendLicense: string;
  onNavChanged: any;
}

export interface NavRoute {
  id: string;
  component: (props?: any) => JSX.Element;
}

export const routes: { [id: string]: NavRoute } = [
  {
    component: IncidentsPage,
    id: 'incidents',
  },
  {
    component: IncidentPage,
    id: 'incident',
  },
  {
    component: UsersPage,
    id: 'users',
  },
  {
    component: IntegrationsPage,
    id: 'integrations',
  },
  {
    component: EscalationsChainsPage,
    id: 'escalations',
  },
  {
    component: SchedulesPage2,
    id: 'schedules',
  },
  {
    component: SchedulesPage,
    id: 'schedules-new',
  },
  {
    component: SchedulePage,
    id: 'schedule',
  },
  {
    component: ChatOpsPage,
    id: 'chat-ops',
  },
  {
    component: OutgoingWebhooks,
    id: 'outgoing_webhooks',
  },
  {
    component: MaintenancePage,
    id: 'maintenance',
  },
  {
    component: SettingsPage,
    id: 'settings',
  },
  {
    component: LiveSettingsPage,
    id: 'live-settings',
  },
  {
    component: OrganizationLogPage,
    id: 'organization-logs',
  },
  {
    component: CloudPage,
    id: 'cloud',
  },
  {
    component: Test,
    id: 'test',
  },
].reduce((prev, current) => {
  prev[current.id] = {
    id: current.id,
    component: current.component,
  };

  return prev;
}, {});
