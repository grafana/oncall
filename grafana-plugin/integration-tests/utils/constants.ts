export const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
export const ONCALL_API_URL = process.env.ONCALL_API_URL || 'http://host.docker.internal:8080';
export const GRAFANA_USERNAME = process.env.GRAFANA_USERNAME || 'oncall';
export const GRAFANA_PASSWORD = process.env.GRAFANA_PASSWORD || 'oncall';
export const MAILSLURP_API_KEY = process.env.MAILSLURP_API_KEY;
export const IS_OPEN_SOURCE = (process.env.IS_OPEN_SOURCE || 'true').toLowerCase() === 'true';
