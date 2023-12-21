import { AppFeature } from 'state/features';

import { Template, TemplateForEdit, commonTemplateForEdit } from './CommonAlertTemplatesForm.config';

export const getTemplatesForEdit = (features: Record<string, boolean>) => {
  if (features[AppFeature.MsTeams]) {
    return Object.assign({}, commonTemplateForEdit, additionalTemplateForEdit);
  }
  return commonTemplateForEdit;
};

const additionalTemplateForEdit: { [id: string]: TemplateForEdit } = {
  msteams_title_template: {
    name: 'msteams_title_template',
    displayName: 'MS Teams title',
    description: '',
    additionalData: {
      chatOpsName: 'msteams',
      chatOpsDisplayName: 'MS Teams',
    },
    type: 'plain',
  },
  msteams_message_template: {
    name: 'msteams_message_template',
    displayName: 'MS Teams message',
    description: '',
    additionalData: {
      chatOpsName: 'msteams',
      chatOpsDisplayName: 'MS Teams',
    },
    type: 'plain',
  },
  msteams_image_url_template: {
    name: 'msteams_image_url_template',
    displayName: 'MS Teams image url',
    description: '',
    additionalData: {
      chatOpsName: 'msteams',
      chatOpsDisplayName: 'MS Teams',
    },
    type: 'plain',
  },
};

export const getTemplatesToRender = (features: Record<string, boolean>) => {
  if (features[AppFeature.MsTeams]) {
    return templatesToRenderWithMsTeams;
  }
  return templatesToRender;
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

export const templatesToRenderWithMsTeams: Template[] = [
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
    name: 'msteams_title_template',
    group: 'microsoft teams',
  },
  {
    name: 'msteams_message_template',
    group: 'microsoft teams',
  },
  {
    name: 'msteams_image_url_template',
    group: 'microsoft teams',
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
