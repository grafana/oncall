import semver from 'semver';

export const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
export const MAILSLURP_API_KEY = process.env.MAILSLURP_API_KEY;

export const GRAFANA_VIEWER_USERNAME = process.env.GRAFANA_VIEWER_USERNAME || 'viewer';
export const GRAFANA_VIEWER_PASSWORD = process.env.GRAFANA_VIEWER_PASSWORD || 'viewer';
export const GRAFANA_EDITOR_USERNAME = process.env.GRAFANA_EDITOR_USERNAME || 'editor';
export const GRAFANA_EDITOR_PASSWORD = process.env.GRAFANA_EDITOR_PASSWORD || 'editor';
export const GRAFANA_ADMIN_USERNAME = process.env.GRAFANA_ADMIN_USERNAME || 'oncall';
export const GRAFANA_ADMIN_PASSWORD = process.env.GRAFANA_ADMIN_PASSWORD || 'oncall';

export const IS_OPEN_SOURCE = (process.env.IS_OPEN_SOURCE || 'true').toLowerCase() === 'true';
export const IS_CLOUD = !IS_OPEN_SOURCE;

export enum OrgRole {
  None = 'None',
  Viewer = 'Viewer',
  Editor = 'Editor',
  Admin = 'Admin',
}

export const MOSCOW_TIMEZONE = 'Europe/Moscow';

export const isGrafanaVersionGreaterThan = (version: string) => semver.gt(process.env.CURRENT_GRAFANA_VERSION, version);
export const isGrafanaVersionLowerThan = (version: string) => semver.lt(process.env.CURRENT_GRAFANA_VERSION, version);
