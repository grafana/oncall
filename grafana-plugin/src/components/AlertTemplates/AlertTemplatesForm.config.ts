import { TemplateForEdit, commonTemplateForEdit } from './CommonAlertTemplatesForm.config';
export interface Template {
  name: string;
  group: string;
}

export const templateForEdit: { [id: string]: TemplateForEdit } = commonTemplateForEdit;

export const templatesToRender: Template[] = [
  {
    name: 'web_title_template',
    group: 'web',
  },
  {
    name: 'slack_title_template',
    group: 'slack',
  },
  {
    name: 'sms_title_template',
    group: 'sms',
  },
  {
    name: 'phone_call_title_template',
    group: 'phone',
  },
  {
    name: 'email_title_template',
    group: 'email',
  },
  {
    name: 'telegram_title_template',
    group: 'telegram',
  },
  {
    name: 'slack_message_template',
    group: 'slack',
  },
  {
    name: 'web_message_template',
    group: 'web',
  },
  {
    name: 'email_message_template',
    group: 'email',
  },
  {
    name: 'telegram_message_template',
    group: 'telegram',
  },
  {
    name: 'slack_image_url_template',
    group: 'slack',
  },
  {
    name: 'web_image_url_template',
    group: 'web',
  },
  {
    name: 'telegram_image_url_template',
    group: 'telegram',
  },
  {
    name: 'grouping_id_template',
    group: 'alert behaviour',
  },
  {
    name: 'acknowledge_condition_template',
    group: 'alert behaviour',
  },
  {
    name: 'resolve_condition_template',
    group: 'alert behaviour',
  },
  {
    name: 'source_link_template',
    group: 'alert behaviour',
  },
];

export const FORM_NAME = 'AlertTemplates';
