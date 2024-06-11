// Custom properties not exposed by OpenAPI schema should be defined here
export type CustomApiSchemas = {
  Webhook: {
    readonly last_response_log?: {
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
    loading?: boolean;
    created_at?: string;
  };
  User: {
    hidden_fields?: boolean;
    display_name?: string;
  };
};
