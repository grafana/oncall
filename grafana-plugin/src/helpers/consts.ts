import { GrafanaBootConfig } from '@grafana/runtime';
import { OnCallAppPluginMeta } from 'app-types';

//@ts-ignore
import plugin from '../../package.json'; // eslint-disable-line

export const PluginId = {
  OnCall: 'grafana-oncall-app',
  Irm: 'grafana-irm-app',
} as const;
export type PluginId = (typeof PluginId)[keyof typeof PluginId];

export const getIsIrmPluginPresent = () => PluginId.Irm in (window.grafanaBootData?.settings as GrafanaBootConfig).apps;

// Determine current environment: cloud, oss or local
const CLOUD_VERSION_REGEX = /^(v\d+\.\d+\.\d+|github-actions-[a-zA-Z0-9-]+)$/;
const determineCurrentEnv = (): 'oss' | 'cloud' | 'local' => {
  if (CLOUD_VERSION_REGEX.test(plugin?.version)) {
    return 'cloud';
  }
  try {
    return process.env.NODE_ENV === 'development' ? 'local' : 'oss';
  } catch (error) {
    return 'cloud';
  }
};
const CURRENT_ENV = determineCurrentEnv();
export const IS_CURRENT_ENV_CLOUD = CURRENT_ENV === 'cloud';
export const IS_CURRENT_ENV_OSS = CURRENT_ENV === 'oss';
export const IS_CURRENT_ENV_LOCAL = CURRENT_ENV === 'local';

export const getPluginId = (): PluginId => {
  try {
    return (process.env.PLUGIN_ID as PluginId) || PluginId.Irm;
  } catch (error) {
    return PluginId.Irm;
  }
};

// Navbar
export const APP_SUBTITLE = `Developer-friendly incident response (${plugin?.version})`;

// height of new Grafana sticky header with breadcrumbs
export const GRAFANA_HEADER_HEIGHT = 80;

export const GRAFANA_LEGACY_SIDEBAR_WIDTH = 56;

// Reusable breakpoint sizes
export const BREAKPOINT_TABS = 1024;

// Default redirect page
export const DEFAULT_PAGE = 'alert-groups';

export const PLUGIN_ROOT = `/a/${getPluginId()}`;
export const PLUGIN_CONFIG = `/plugins/${getPluginId()}`;

export const REQUEST_HELP_URL = 'https://grafana.com/profile/org/tickets/new';

// Environment options list for onCallApiUrl
export const ONCALL_PROD = 'https://oncall-prod-us-central-0.grafana.net/oncall';
export const ONCALL_OPS = 'https://oncall-ops-eu-south-0.grafana.net/oncall';
export const ONCALL_DEV = 'https://oncall-dev-us-central-0.grafana.net/oncall';

export const getOnCallApiUrl = (meta?: OnCallAppPluginMeta) => meta?.jsonData?.onCallApiUrl;

export const getProcessEnvVarSafely = (name: string) => {
  try {
    return process.env[name];
  } catch (error) {
    console.error(error);
    return undefined;
  }
};

const getGrafanaSubUrl = () => {
  try {
    return window.grafanaBootData.settings.appSubUrl || '';
  } catch (_err) {
    return '';
  }
};

export const getOnCallApiPath = (subpath = '') => {
  // We need to consider the grafanaSubUrl in case Grafana is served from subpath, e.g. http://localhost:3000/grafana
  return `${getGrafanaSubUrl()}/api/plugins/${getPluginId()}/resources${subpath}`;
};

// Faro
export const FARO_ENDPOINT_DEV =
  'https://faro-collector-prod-us-central-0.grafana.net/collect/fb03e474a96cf867f4a34590c002984c';
export const FARO_ENDPOINT_OPS =
  'https://faro-collector-prod-us-central-0.grafana.net/collect/40ccaafad6b71aa90fc53c3b0a1adb31';
export const FARO_ENDPOINT_PROD =
  'https://faro-collector-prod-us-central-0.grafana.net/collect/03a11ed03c3af04dcfc3be9755f2b053';

export const DOCS_ROOT = 'https://grafana.com/docs/oncall/latest';
export const DOCS_SLACK_SETUP = 'https://grafana.com/docs/oncall/latest/open-source/#slack-setup';
export const DOCS_TELEGRAM_SETUP = 'https://grafana.com/docs/oncall/latest/notify/telegram/';
export const DOCS_SERVICE_ACCOUNTS = 'https://grafana.com/docs/grafana/latest/administration/service-accounts/';
export const DOCS_ONCALL_OSS_INSTALL =
  'https://grafana.com/docs/oncall/latest/set-up/open-source/#install-grafana-oncall-oss';
export const DOCS_MATTERMOST_SETUP = 'https://grafana.com/docs/oncall/latest/manage/notify/mattermost/';

export const generateAssignToTeamInputDescription = (objectName: string): string =>
  `Assigning to a team allows you to filter ${objectName} and configure their visibility. Go to OnCall -> Settings -> Team and Access Settings for more details.`;

export enum PAGE {
  Integrations = 'integrations',
  Escalations = 'escalation_chains',
  Incidents = 'incidents',
  Webhooks = 'webhooks',
  Schedules = 'schedules',
  Users = 'users',
}

export const TEXT_ELLIPSIS_CLASS = 'overflow-child';

export const INCIDENT_HORIZONTAL_SCROLLING_STORAGE = 'isIncidentalTableHorizontalScrolling';
export const IRM_TAB = 'IRM';

export enum OnCallAGStatus {
  Firing = 'firing',
  Resolved = 'resolved',
  Silenced = 'silenced',
  Acknowledged = 'acknowledged',
}

export const GENERIC_ERROR = 'An error has occurred. Please try again';
export const PROCESSING_REQUEST_ERROR = 'There was an error processing your request. Please try again';

export const INTEGRATION_SERVICENOW = 'servicenow';

export const StackSize: Record<'none' | 'xs' | 'sm' | 'md' | 'lg', 0 | 0.5 | 1 | 2 | 3> = {
  none: 0,
  xs: 0.5,
  sm: 1,
  md: 2,
  lg: 3,
};
