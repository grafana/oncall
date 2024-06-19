export enum ActionKey {
  VERIFY_PLUGIN_CONNECTION = 'VERIFY_PLUGIN_CONNECTION',
  UPDATE_SETTINGS_AND_REINITIALIZE_PLUGIN = 'UPDATE_SETTINGS_AND_REINITIALIZE_PLUGIN',
  RECREATE_SERVICE_ACCOUNT = 'RECREATE_SERVICE_ACCOUNT',
  UPDATE_INTEGRATION = 'UPDATE_INTEGRATION',
  ADD_NEW_COLUMN_TO_ALERT_GROUP = 'ADD_NEW_COLUMN_TO_ALERT_GROUP',
  REMOVE_COLUMN_FROM_ALERT_GROUP = 'REMOVE_COLUMN_FROM_ALERT_GROUP',
  RESET_COLUMNS_FROM_ALERT_GROUP = 'RESET_COLUMNS_FROM_ALERT_GROUP',
  UPDATE_PERSONAL_EVENTS = 'UPDATE_PERSONAL_EVENTS',
  UPDATE_ALERT_GROUP = 'UPDATE_ALERT_GROUP',
  FETCH_INCIDENTS = 'FETCH_INCIDENTS',
  FETCH_INCIDENTS_POLLING = 'FETCH_INCIDENTS_POLLING',
  FETCH_INCIDENTS_AND_STATS = 'FETCH_INCIDENTS_AND_STATS',
  INCIDENTS_BULK_UPDATE = 'INCIDENTS_BULK_UPDATE',

  UPDATE_FILTERS_AND_FETCH_INCIDENTS = 'UPDATE_FILTERS_AND_FETCH_INCIDENTS',
  UPDATE_SERVICENOW_TOKEN = 'UPDATE_SERVICENOW_TOKEN',
  FETCH_INTEGRATIONS = 'FETCH_INTEGRATIONS',
  TEST_CALL_OR_SMS = 'TEST_CALL_OR_SMS',
  FETCH_INTEGRATION_CHANNELS = 'FETCH_INTEGRATION_CHANNELS',
  CONNECT_INTEGRATION_CHANNELS = 'CONNECT_INTEGRATION_CHANNELS',
  FETCH_INTEGRATIONS_AVAILABLE_FOR_CONNECTION = 'FETCH_INTEGRATIONS_AVAILABLE_FOR_CONNECTION',
}
