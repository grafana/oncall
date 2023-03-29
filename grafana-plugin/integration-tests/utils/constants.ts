export const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
export const ONCALL_API_URL = process.env.ONCALL_API_URL || 'http://host.docker.internal:8080';
export const MAILSLURP_API_KEY = process.env.MAILSLURP_API_KEY;
export const IS_OPEN_SOURCE = (process.env.IS_OPEN_SOURCE || 'true').toLowerCase() === 'true';

export const GRAFANA_ADMIN_USERNAME = process.env.GRAFANA_ADMIN_USERNAME || 'oncall';
export const GRAFANA_ADMIN_PASSWORD = process.env.GRAFANA_ADMIN_PASSWORD || 'oncall';

export const GRAFANA_VIEWER_USERNAME = 'oncall-viewer';
export const GRAFANA_VIEWER_PASSWORD = 'oncall';
