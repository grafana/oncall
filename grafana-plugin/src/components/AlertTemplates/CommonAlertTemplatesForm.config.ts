import { TemplateOptions } from 'pages/integration_2/Integration2.config';

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

export const commonTemplateForEdit: { [id: string]: TemplateForEdit } = {
  web_title_template: {
    displayName: 'Web title',
    name: TemplateOptions.WebTitle.key,
    description: ''
  },
  web_message_template: {
    displayName: 'Web message',
    name: TemplateOptions.WebMessage.key,
    description: ''
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
    description: '',
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
