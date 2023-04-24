import plugin from '../../package.json'; // eslint-disable-line

// Navbar
export const APP_TITLE = 'Grafana OnCall';
export const APP_SUBTITLE = `Developer-friendly incident response (${plugin?.version})`;

// License
export const GRAFANA_LICENSE_OSS = 'OpenSource';

// Reusable breakpoint sizes
export const BREAKPOINT_TABS = 1024;

// Default redirect page
export const DEFAULT_PAGE = 'alert-groups';

export const PLUGIN_ROOT = '/a/grafana-oncall-app';

// Environment options list for onCallApiUrl
export const ONCALL_PROD = 'https://oncall-prod-us-central-0.grafana.net/oncall';
export const ONCALL_OPS = 'https://oncall-ops-us-east-0.grafana.net/oncall';
export const ONCALL_DEV = 'https://oncall-dev-us-central-0.grafana.net/oncall';

// Faro
export const FARO_ENDPOINT_DEV =
  'https://faro-collector-prod-us-central-0.grafana.net/collect/fb03e474a96cf867f4a34590c002984c';
export const FARO_ENDPOINT_OPS =
  'https://faro-collector-prod-us-central-0.grafana.net/collect/40ccaafad6b71aa90fc53c3b0a1adb31';
export const FARO_ENDPOINT_PROD =
  'https://faro-collector-prod-us-central-0.grafana.net/collect/03a11ed03c3af04dcfc3be9755f2b053';

export const DOCS_SLACK_SETUP = 'https://grafana.com/docs/oncall/latest/open-source/#slack-setup';
export const DOCS_TELEGRAM_SETUP = 'https://grafana.com/docs/oncall/latest/chat-options/configure-telegram/';

// Make sure if you chage max-width here you also change it in responsive.css
export const TABLE_COLUMN_MAX_WIDTH = 1500;
