import { TemplateOptions } from 'pages/integration_2/Integration2.config';

import { TemplateForEdit, commonTemplateForEdit } from './CommonAlertTemplatesForm.config';
export interface Template {
  name: string;
  group: string;
}

export const templateForEdit: { [id: string]: TemplateForEdit } = commonTemplateForEdit;

export const templateForEdit: { [id: string]: TemplateForEdit } = {
  web_title_template: {
    displayName: 'Web title',
    name: TemplateOptions.WebTitle.key,
    description:
      'Same for: phone call, sms, mobile push, mobile app title, email title, slack title, ms teams title, telegram title.',
  },
  web_message_template: {
    displayName: 'Web message',
    name: TemplateOptions.WebMessage.key,
    description:
      'Same for: phone call, sms, mobile push, mobile app title, email title, slack title, ms teams title, telegram title.',
  },
  slack_title_template: {
    name: 'slack_title_template',
    displayName: TemplateOptions.SlackTitle.key,
    description: '',
    additionalData: {
      chatOpsName: 'slack',
      data: 'Click "Acknowledge" and then "Unacknowledge" in Slack to trigger re-rendering.',
    },
  },
  sms_title_template: {
    name: TemplateOptions.SMS.key,
    displayName: 'Sms title',
    description: '',
  },
  phone_call_title_template: {
    name: TemplateOptions.Phone.key,
    displayName: 'Phone call title',
    description: '',
  },
  email_title_template: {
    name: TemplateOptions.EmailTitle.key,
    displayName: 'Email title',
    description: '',
  },
  telegram_title_template: {
    name: TemplateOptions.TelegramTitle.key,
    displayName: 'Telegram title',
    description: '',
    additionalData: {
      chatOpsName: 'telegram',
    },
  },
  slack_message_template: {
    name: TemplateOptions.SlackMessage.key,
    displayName: 'Slack message',
    description: '',
    additionalData: {
      chatOpsName: 'slack',
      data: 'Click "Acknowledge" and then "Unacknowledge" in Slack to trigger re-rendering.',
    },
  },
  email_message_template: {
    name: TemplateOptions.EmailMessage.key,
    displayName: 'Email message',
    description: '',
  },
  telegram_message_template: {
    name: TemplateOptions.TelegramMessage.key,
    displayName: 'Telegram message',
    description: '',
    additionalData: {
      chatOpsName: 'telegram',
    },
  },
  slack_image_url_template: {
    name: TemplateOptions.SlackImage.key,
    displayName: 'Slack image url',
    description: '',
    additionalData: {
      chatOpsName: 'slack',
      data: 'Click "Acknowledge" and then "Unacknowledge" in Slack to trigger re-rendering.',
    },
  },
  web_image_url_template: {
    name: TemplateOptions.WebImage.key,
    displayName: 'Web image url',
    description:
      'Same for: phone call, sms, mobile push, mobile app title, email title, slack title, ms teams title, telegram title.',
  },
  telegram_image_url_template: {
    name: TemplateOptions.TelegramImage.key,
    displayName: 'Telegram image url',
    description: '',
    additionalData: {
      chatOpsName: 'telegram',
    },
  },
  grouping_id_template: {
    name: TemplateOptions.Grouping.key,
    displayName: 'Grouping',
    description:
      'Reduce noise, minimize duplication with Alert Grouping, based on time, alert content, and even multiple features at the same time.  Check the cheasheet to customize your template.',
  },
  acknowledge_condition_template: {
    name: TemplateOptions.Autoacknowledge.key,
    displayName: 'Acknowledge condition',
    description: '',
  },
  resolve_condition_template: {
    name: TemplateOptions.Resolve.key,
    displayName: 'Resolve condition',
    description:
      'When monitoring systems return to normal, they can send "resolve" alerts. OnCall can use these signals to resolve alert groups accordingly.',
  },
  source_link_template: {
    name: TemplateOptions.SourceLink.key,
    displayName: 'Source link',
    description: '',
  },
  route_template: {
    name: TemplateOptions.Routing.key,
    displayName: 'Routing',
    description:
      'Routes direct alerts to different escalation chains based on the content, such as severity or region.',
    additionalData: {
      additionalDescription: 'For an alert to be directed to this route, the template must evaluate to True.',
      data: 'Selected Alert will be directed to this route',
    },
    isRoute: true,
  },
};

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
