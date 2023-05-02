import { KeyValuePair } from 'utils';

export const TEXTAREA_ROWS_COUNT = 4;
export const MAX_CHARACTERS_COUNT = 50;

export const MONACO_OPTIONS = {
  renderLineHighlight: false,
  readOnly: true,
  scrollbar: {
    vertical: 'hidden',
    horizontal: 'hidden',
    verticalScrollbarSize: 0,
    handleMouseWheel: false,
  },
  hideCursorInOverviewRuler: true,
  minimap: { enabled: false },
  cursorStyle: {
    display: 'none',
  },
};

export const INTEGRATION_DEMO_PAYLOAD = {
  alert_uid: '08d6891a-835c-e661-39fa-96b6a9e26552',
  title: 'The whole system is down',
  image_url: 'https://http.cat/500',
  state: 'alerting',
  link_to_upstream_details: 'https://en.wikipedia.org/wiki/Downtime',
  message: 'Smth happened. Oh no!',
};

export const MONACO_INPUT_HEIGHT_SMALL = '32px';
export const MONACO_INPUT_HEIGHT_TALL = '120px';

const TemplateOptions = {
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
  /*Should it be in Oncallprivate repo? (All MsTeams)*/
  MSTeamsTitle: new KeyValuePair('MSTeams Title', 'Title'),
  MSTeamsMessage: new KeyValuePair('MSTeams Message', 'Message'),
  MSTeamsImage: new KeyValuePair('MSTeams Image', 'Image'),

  Email: new KeyValuePair('Email', 'Email'),
  Slack: new KeyValuePair('Slack', 'Slack'),
  MSTeams: new KeyValuePair('Microsoft Teams', 'Microsoft Teams'),
  Telegram: new KeyValuePair('Telegram', 'Telegram'),
};

export const INTEGRATION_TEMPLATES_LIST = [
  {
    label: TemplateOptions.SourceLink.value,
    value: TemplateOptions.SourceLink.key,
  },
  {
    label: TemplateOptions.Autoacknowledge.value,
    value: TemplateOptions.Autoacknowledge.key,
  },
  {
    label: TemplateOptions.Phone.value,
    value: TemplateOptions.Phone.key,
  },
  {
    label: TemplateOptions.SMS.value,
    value: TemplateOptions.SMS.key,
  },
  {
    label: TemplateOptions.Email.value,
    value: TemplateOptions.Email.key,
    children: [
      {
        label: TemplateOptions.EmailTitle.value,
        value: TemplateOptions.EmailTitle.key,
      },
      {
        label: TemplateOptions.EmailMessage.value,
        value: TemplateOptions.EmailMessage.key,
      },
    ],
  },
  {
    label: TemplateOptions.Slack.value,
    value: TemplateOptions.Slack.key,
    children: [
      {
        label: TemplateOptions.SlackTitle.value,
        value: TemplateOptions.SlackTitle.key,
      },
      {
        label: TemplateOptions.SlackMessage.value,
        value: TemplateOptions.SlackMessage.key,
      },
      {
        label: TemplateOptions.SlackImage.value,
        value: TemplateOptions.SlackImage.key,
      },
    ],
  },
  {
    label: TemplateOptions.MSTeams.value,
    value: TemplateOptions.MSTeams.key,
    children: [
      {
        label: TemplateOptions.MSTeamsTitle.value,
        value: TemplateOptions.MSTeamsTitle.key,
      },
      {
        label: TemplateOptions.MSTeamsMessage.value,
        value: TemplateOptions.MSTeamsMessage.key,
      },
      {
        label: TemplateOptions.MSTeamsImage.value,
        value: TemplateOptions.MSTeamsImage.key,
      },
    ],
  },
  {
    label: TemplateOptions.Telegram.value,
    value: TemplateOptions.Telegram.key,
    children: [
      {
        label: TemplateOptions.TelegramTitle.value,
        value: TemplateOptions.TelegramTitle.key,
      },
      {
        label: TemplateOptions.TelegramMessage.value,
        value: TemplateOptions.TelegramMessage.key,
      },
      {
        label: TemplateOptions.TelegramImage.value,
        value: TemplateOptions.TelegramImage.key,
      },
    ],
  },
];
