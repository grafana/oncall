import { KeyValuePair } from 'utils';

export const TEXTAREA_ROWS_COUNT = 4;
export const MAX_CHARACTERS_COUNT = 50;

export const MONACO_INPUT_HEIGHT_SMALL = '32px';
export const MONACO_INPUT_HEIGHT_TALL = '120px';

export const BaseTemplateOptions = {
  WebTitle: new KeyValuePair('web_title_template', 'Web Title'),
  WebMessage: new KeyValuePair('web_message_template', 'Web Message'),
  WebImage: new KeyValuePair('web_image_url_template', 'Web Image'),
  Grouping: new KeyValuePair('grouping_id_template', 'Grouping'),
  Resolve: new KeyValuePair('resolve_condition_template', 'Resolve condition'),
  Routing: new KeyValuePair('route_template', 'Routing'),

  SourceLink: new KeyValuePair('source_link_template', 'Source Link'),
  Autoacknowledge: new KeyValuePair('acknowledge_condition_template', 'Autoacknowledge'),
  Phone: new KeyValuePair('phone_call_title_template', 'Phone'),
  SMS: new KeyValuePair('sms_title_template', 'SMS'),
  SlackTitle: new KeyValuePair('slack_title_template', 'Title'),
  SlackMessage: new KeyValuePair('slack_message_template', 'Message'),
  SlackImage: new KeyValuePair('slack_image_url_template', 'Image'),
  EmailTitle: new KeyValuePair('email_title_template', 'Title'),
  EmailMessage: new KeyValuePair('email_message_template', 'Message'),
  TelegramTitle: new KeyValuePair('telegram_title_template', 'Title'),
  TelegramMessage: new KeyValuePair('telegram_message_template', 'Message'),
  TelegramImage: new KeyValuePair('telegram_image_url_template', 'Image'),

  Email: new KeyValuePair('Email', 'Email'),
  Slack: new KeyValuePair('Slack', 'Slack'),
  MSTeams: new KeyValuePair('Microsoft Teams', 'Microsoft Teams'),
  Telegram: new KeyValuePair('Telegram', 'Telegram'),
};

export const BASE_INTEGRATION_TEMPLATES_LIST = [
  {
    label: BaseTemplateOptions.SourceLink.value,
    value: BaseTemplateOptions.SourceLink.key,
  },
  {
    label: BaseTemplateOptions.Autoacknowledge.value,
    value: BaseTemplateOptions.Autoacknowledge.key,
  },
  {
    label: BaseTemplateOptions.Phone.value,
    value: BaseTemplateOptions.Phone.key,
  },
  {
    label: BaseTemplateOptions.SMS.value,
    value: BaseTemplateOptions.SMS.key,
  },
  {
    label: BaseTemplateOptions.Email.value,
    value: BaseTemplateOptions.Email.key,
    children: [
      {
        label: BaseTemplateOptions.EmailTitle.value,
        value: BaseTemplateOptions.EmailTitle.key,
      },
      {
        label: BaseTemplateOptions.EmailMessage.value,
        value: BaseTemplateOptions.EmailMessage.key,
      },
    ],
  },
  {
    label: BaseTemplateOptions.Slack.value,
    value: BaseTemplateOptions.Slack.key,
    children: [
      {
        label: BaseTemplateOptions.SlackTitle.value,
        value: BaseTemplateOptions.SlackTitle.key,
      },
      {
        label: BaseTemplateOptions.SlackMessage.value,
        value: BaseTemplateOptions.SlackMessage.key,
      },
      {
        label: BaseTemplateOptions.SlackImage.value,
        value: BaseTemplateOptions.SlackImage.key,
      },
    ],
  },
  {
    label: BaseTemplateOptions.Telegram.value,
    value: BaseTemplateOptions.Telegram.key,
    children: [
      {
        label: BaseTemplateOptions.TelegramTitle.value,
        value: BaseTemplateOptions.TelegramTitle.key,
      },
      {
        label: BaseTemplateOptions.TelegramMessage.value,
        value: BaseTemplateOptions.TelegramMessage.key,
      },
      {
        label: BaseTemplateOptions.TelegramImage.value,
        value: BaseTemplateOptions.TelegramImage.key,
      },
    ],
  },
];
