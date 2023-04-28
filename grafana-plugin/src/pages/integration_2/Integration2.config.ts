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

export const TemplateOptions = {
  SourceLink: new KeyValuePair('Source Link', 'Source Link'),
  Autoacknowledge: new KeyValuePair('Autoacknowledge', 'Autoacknowledge'),
  Phone: new KeyValuePair('Phone', 'Phone'),
  SMS: new KeyValuePair('SMS', 'SMS'),
  SlackTitle: new KeyValuePair('Slack Title', 'Title'),
  SlackMessage: new KeyValuePair('Slack Message', 'Message'),
  SlackImage: new KeyValuePair('Slack Image', 'Image'),
  EmailTitle: new KeyValuePair('Email Title', 'Title'),
  EmailMessage: new KeyValuePair('Email Message', 'Message'),
  TelegramTitle: new KeyValuePair('Telegram Title', 'Title'),
  TelegramMessage: new KeyValuePair('Telegram Message', 'Message'),
  TelegramImage: new KeyValuePair('Telegram Image', 'Image'),
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
