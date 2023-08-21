import EscalationsChainsPage from 'pages/escalation-chains/EscalationChains';
import IncidentPage from 'pages/incident/Incident';
import IncidentsPage from 'pages/incidents/Incidents';
import MaintenancePage from 'pages/maintenance/Maintenance';
import OutgoingWebhooks from 'pages/outgoing_webhooks/OutgoingWebhooks';
import SchedulePage from 'pages/schedule/Schedule';
import SchedulesPage from 'pages/schedules/Schedules';
import SettingsPage from 'pages/settings/SettingsPage';
import ChatOpsPage from 'pages/settings/tabs/ChatOps/ChatOps';
import CloudPage from 'pages/settings/tabs/Cloud/CloudPage';
import LiveSettingsPage from 'pages/settings/tabs/LiveSettings/LiveSettingsPage';
import UsersPage from 'pages/users/Users';

import IntegrationsPage2 from './integrations/Integrations';

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
    component: IntegrationsPage2,
    id: 'integrations',
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
