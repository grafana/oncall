export interface AlertTemplatesDTO {
  slack_title_template: string;
  web_title_template: string;
  sms_title_template: string;
  phone_call_title_template: string;
  email_title_template: string;
  telegram_title_template: string;
  slack_message_template: string;
  web_message_template: string;
  email_message_template: string;
  telegram_message_template: string;
  slack_image_url_template: string;
  web_image_url_template: string;
  telegram_image_url_template: string;
  grouping_id_template: string;
  resolve_condition_template: string;
  acknowledge_condition_template: string;
  payload_example: string;
}
