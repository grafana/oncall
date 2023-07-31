import { TemplateOptions } from 'pages/integration/Integration.config';

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
    chatOpsDisplayName?: string;
    data?: string;
    additionalDescription?: string;
  };
  isRoute?: boolean;
  type?: 'html' | 'plain' | 'image' | 'boolean';
}

export const commonTemplateForEdit: { [id: string]: TemplateForEdit } = {
  web_title_template: {
    displayName: 'Web title',
    name: TemplateOptions.WebTitle.key,
    description: '',
    type: 'html',
  },
  web_message_template: {
    displayName: 'Web message',
    name: TemplateOptions.WebMessage.key,
    description: '',
    type: 'html',
  },
  slack_title_template: {
    displayName: 'Slack title',
    name: TemplateOptions.SlackTitle.key,
    description: '',
    additionalData: {
      chatOpsName: 'slack',
      chatOpsDisplayName: 'Slack',
      data: 'Click "Acknowledge" and then "Unacknowledge" in Slack to trigger re-rendering.',
    },
    type: 'plain',
  },
  sms_title_template: {
    name: TemplateOptions.SMS.key,
    displayName: 'Sms title',
    description:
      "Result of this template will be used as title of SMS message. Please don't include any urls, or phone numbers, to avoid SMS message being blocked by carriers.",
    type: 'plain',
  },
  phone_call_title_template: {
    name: TemplateOptions.Phone.key,
    displayName: 'Phone Call title',
    description: '',
    type: 'plain',
  },
  email_title_template: {
    name: TemplateOptions.EmailTitle.key,
    displayName: 'Email title',
    description: '',
    type: 'plain',
  },
  telegram_title_template: {
    name: TemplateOptions.TelegramTitle.key,
    displayName: 'Telegram title',
    description: '',
    additionalData: {
      chatOpsName: 'telegram',
      chatOpsDisplayName: 'Telegram',
    },
    type: 'plain',
  },
  slack_message_template: {
    name: TemplateOptions.SlackMessage.key,
    displayName: 'Slack message',
    description: '',
    additionalData: {
      chatOpsName: 'slack',
      chatOpsDisplayName: 'Slack',
      data: 'Click "Acknowledge" and then "Unacknowledge" in Slack to trigger re-rendering.',
    },
    type: 'plain',
  },
  email_message_template: {
    name: TemplateOptions.EmailMessage.key,
    displayName: 'Email message',
    description: '',
    type: 'plain',
  },
  telegram_message_template: {
    name: TemplateOptions.TelegramMessage.key,
    displayName: 'Telegram message',
    description: '',
    additionalData: {
      chatOpsName: 'telegram',
      chatOpsDisplayName: 'Telegram',
    },
    type: 'plain',
  },
  slack_image_url_template: {
    name: TemplateOptions.SlackImage.key,
    displayName: 'Slack image url',
    description: '',
    additionalData: {
      chatOpsName: 'slack',
      chatOpsDisplayName: 'Slack',
      data: 'Click "Acknowledge" and then "Unacknowledge" in Slack to trigger re-rendering.',
    },
    type: 'plain',
  },
  web_image_url_template: {
    name: TemplateOptions.WebImage.key,
    displayName: 'Web image url',
    description: '',
    type: 'image',
  },
  telegram_image_url_template: {
    name: TemplateOptions.TelegramImage.key,
    displayName: 'Telegram image url',
    description: '',
    additionalData: {
      chatOpsName: 'telegram',
      chatOpsDisplayName: 'Telegram',
    },
    type: 'image',
  },
  grouping_id_template: {
    name: TemplateOptions.Grouping.key,
    displayName: 'Grouping',
    description:
      'Reduce noise, minimize duplication with Alert Grouping, based on time, alert content, and even multiple features at the same time.  Check the cheasheet to customize your template.',
    type: 'plain',
  },
  acknowledge_condition_template: {
    name: TemplateOptions.Autoacknowledge.key,
    displayName: 'Acknowledge condition',
    description: '',
    type: 'boolean',
  },
  resolve_condition_template: {
    name: TemplateOptions.Resolve.key,
    displayName: 'Resolve condition',
    description:
      'When monitoring systems return to normal, they can send "resolve" alerts. OnCall can use these signals to resolve alert groups accordingly.',
    type: 'boolean',
  },
  source_link_template: {
    name: TemplateOptions.SourceLink.key,
    displayName: 'Source link',
    description: '',
    type: 'plain',
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
    type: 'boolean',
  },
};
