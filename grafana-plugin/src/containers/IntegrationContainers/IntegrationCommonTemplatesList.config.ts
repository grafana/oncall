import { MONACO_INPUT_HEIGHT_SMALL, MONACO_INPUT_HEIGHT_TALL } from 'pages/integration_2/Integration2.config';

interface TemplateToRender {
  name: string;
  label: string;
  height: string;
  labelTooltip?: string;
}

export interface TemplateBlock {
  name: string;
  contents: TemplateToRender[];
}

export const commonTemplatesToRender: TemplateBlock[] = [
  {
    name: null,
    contents: [
      {
        name: 'grouping_id_template',
        label: 'Grouping',
        labelTooltip:
          'The Grouping Template is applied to every incoming alert payload after the Routing Template. It can be based on time, or alert content, or both. If the resulting grouping key matches an existing non-resolved alert group, the alert will be grouped accordingly. Otherwise, a new alert group will be created',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
      {
        name: 'resolve_condition_template',
        label: 'Autoresolution',
        labelTooltip:
          'If Autoresolution Template is True, the alert will resolve its group as "resolved by source". If the group is already resolved, the alert will be added to that group.',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
    ],
  },
  {
    name: 'Web',
    contents: [
      {
        name: 'web_title_template',
        label: 'Title',
        height: MONACO_INPUT_HEIGHT_TALL,
      },
      {
        name: 'web_message_template',
        label: 'Message',
        height: MONACO_INPUT_HEIGHT_TALL,
      },
      {
        name: 'web_image_url_template',
        label: 'Image',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
    ],
  },
  {
    name: null,
    contents: [
      {
        name: 'acknowledge_condition_template',
        label: 'Auto acknowledge',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
      {
        name: 'source_link_template',
        label: 'Source link',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
    ],
  },
  {
    name: null,
    contents: [
      {
        name: 'phone_call_title_template',
        label: 'Phone Call',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
      {
        name: 'sms_title_template',
        label: 'SMS',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
    ],
  },
  {
    name: 'Slack',
    contents: [
      {
        name: 'slack_title_template',
        label: 'Title',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
      {
        name: 'slack_message_template',
        label: 'Message',
        height: MONACO_INPUT_HEIGHT_TALL,
      },
      {
        name: 'slack_image_url_template',
        label: 'Image',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
    ],
  },
  {
    name: 'Telegram',
    contents: [
      {
        name: 'telegram_title_template',
        label: 'Title',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
      {
        name: 'telegram_message_template',
        label: 'Message',
        height: MONACO_INPUT_HEIGHT_TALL,
      },
      {
        name: 'telegram_image_url_template',
        label: 'Image',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
    ],
  },
  {
    name: 'Email',
    contents: [
      {
        name: 'email_title_template',
        label: 'Title',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
      { name: 'email_message_template', label: 'Message', height: MONACO_INPUT_HEIGHT_TALL },
    ],
  },
];
