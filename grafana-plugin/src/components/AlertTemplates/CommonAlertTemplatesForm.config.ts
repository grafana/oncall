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
    name: 'web_title_template',
    description: '',
  },
  web_message_template: {
    displayName: 'Web message',
    name: 'web_message_template',
    description: '',
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
    description: '',
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
    additionalData: {
      data: 'Alerts with this Grouping ID are grouped together',
    },
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
      'When monitoring systems return to normal, they can send "resolve" alerts. If Autoresolution Template is True, the alert will resolve its group as "resolved by source". If the group is already resolved, the alert will be added to that group',
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
