import { AlertAction, TimeLineItem } from 'models/alertgroup/alertgroup.types';

// Custom properties not exposed by OpenAPI schema should be defined here
export type CustomApiSchemas = {
  Webhook: {
    last_response_log?: {
      timestamp: string;
      url: string;
      request_trigger: string;
      request_headers: string;
      request_data: string;
      status_code: string;
      content: string;
      event_data: string;
    };
  };
  AlertGroup: {
    title: string; // TODO: check with backend
    undoAction: AlertAction; // TODO: check with backend
    loading?: boolean; // TODO: check with backend
    created_at?: string; // TODO: check with backend
    render_after_resolve_report_json?: TimeLineItem[];
  };
};
