import EscalationsChainsPage from 'pages/escalation-chains/EscalationChains';
import IncidentPage from 'pages/incident/Incident';
import IncidentsPage from 'pages/incidents/Incidents';
// import IntegrationsPage from 'pages/integrations/Integrations';
import MaintenancePage from 'pages/maintenance/Maintenance';
import OrganizationLogPage from 'pages/organization-logs/OrganizationLog';
import OutgoingWebhooks from 'pages/outgoing_webhooks/OutgoingWebhooks';
import OutgoingWebhooks2 from 'pages/outgoing_webhooks_2/OutgoingWebhooks2';
import SchedulePage from 'pages/schedule/Schedule';
import SchedulesPage from 'pages/schedules/Schedules';
import SettingsPage from 'pages/settings/SettingsPage';
import ChatOpsPage from 'pages/settings/tabs/ChatOps/ChatOps';
import CloudPage from 'pages/settings/tabs/Cloud/CloudPage';
import LiveSettingsPage from 'pages/settings/tabs/LiveSettings/LiveSettingsPage';
import UsersPage from 'pages/users/Users';

import IntegrationsPage2 from './integrations_2/Integrations2';

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
  // {
  //   component: IntegrationsPage,
  //   id: 'integrations',
  // },
  {
    component: IntegrationsPage2,
    id: 'integrations_2',
  },
  {
    component: EscalationsChainsPage,
    id: 'escalations',
  },
  {
    component: SchedulesPage,
    id: 'schedules',
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
    component: OutgoingWebhooks2,
    id: 'outgoing_webhooks_2',
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
].reduce((prev, current) => {
  prev[current.id] = {
    id: current.id,
    component: current.component,
  };

  return prev;
}, {});
