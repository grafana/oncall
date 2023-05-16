export interface Template {
  name: string;
  group: string;
}

export interface TemplateForEdit {
  displayName: string;
  name: string;
  description?: string;
  additionalData?: {
    chatOpsName?: string;
    data?: string;
    additionalDescription?: string;
  };
  isRoute?: boolean;
}

export const templateForEdit: { [id: string]: TemplateForEdit } = {
  web_title_template: {
    displayName: 'Web title',
    name: 'web_title_template',
    description:
      'Same for: phone call, sms, mobile push, mobile app title, email title, slack title, ms teams title, telegram title.',
  },
  web_message_template: {
    displayName: 'Web message',
    name: 'web_message_template',
    description:
      'Same for: phone call, sms, mobile push, mobile app title, email title, slack title, ms teams title, telegram title.',
  },
  slack_title_template: {
    name: 'slack_title_template',
    displayName: 'Slack title',
    description: '',
    additionalData: {
      chatOpsName: 'slack',
      data: 'Click "Acknowledge" and then "Unacknowledge" in Slack to trigger re-rendering.',
    },
  },
  sms_title_template: {
    name: 'sms_title_template',
    displayName: 'Sms title',
    description: '',
  },
  phone_call_title_template: {
    name: 'phone_call_title_template',
    displayName: 'Phone call title',
    description: '',
  },
  email_title_template: {
    name: 'email_title_template',
    displayName: 'Email title',
    description: '',
  },
  telegram_title_template: {
    name: 'telegram_title_template',
    displayName: 'Telegram title',
    description: '',
    additionalData: {
      chatOpsName: 'telegram',
    },
  },
  slack_message_template: {
    name: 'slack_message_template',
    displayName: 'Slack message',
    description: '',
    additionalData: {
      chatOpsName: 'slack',
      data: 'Click "Acknowledge" and then "Unacknowledge" in Slack to trigger re-rendering.',
    },
  },
  email_message_template: {
    name: 'email_message_template',
    displayName: 'Email message',
    description: '',
  },
  telegram_message_template: {
    name: 'telegram_message_template',
    displayName: 'Telegram message',
    description: '',
    additionalData: {
      chatOpsName: 'telegram',
    },
  },
  slack_image_url_template: {
    name: 'slack_image_url_template',
    displayName: 'Slack image url',
    description: '',
    additionalData: {
      chatOpsName: 'slack',
      data: 'Click "Acknowledge" and then "Unacknowledge" in Slack to trigger re-rendering.',
    },
  },
  web_image_url_template: {
    name: 'web_image_url_template',
    displayName: 'Web image url',
    description:
      'Same for: phone call, sms, mobile push, mobile app title, email title, slack title, ms teams title, telegram title.',
  },
  telegram_image_url_template: {
    name: 'telegram_image_url_template',
    displayName: 'Telegram image url',
    description: '',
    additionalData: {
      chatOpsName: 'telegram',
    },
  },
  grouping_id_template: {
    name: 'grouping_id_template',
    displayName: 'Grouping',
    description:
      'Reduce noise, minimize duplication with Alert Grouping, based on time, alert content, and even multiple features at the same time.  Check the cheasheet to customize your template.',
  },
  acknowledge_condition_template: {
    name: 'acknowledge_condition_template',
    displayName: 'Acknowledge condition',
    description: '',
  },
  resolve_condition_template: {
    name: 'resolve_condition_template',
    displayName: 'Resolve condition',
    description:
      'When monitoring systems return to normal, they can send "resolve" alerts. OnCall can use these signals to resolve alert groups accordingly.',
  },
  source_link_template: {
    name: 'source_link_template',
    displayName: 'Source link',
    description: '',
  },
  route_template: {
    name: 'route_template',
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
