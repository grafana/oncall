import { AppFeature } from 'state/features';

import { TemplateForEdit, commonTemplateForEdit } from './CommonAlertTemplatesForm.config';

export const getTemplatesForEdit = (features: Record<string, boolean>) => {
  if (features?.[AppFeature.MsTeams]) {
    return { ...commonTemplateForEdit, ...additionalTemplateForEdit };
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

export const FORM_NAME = 'AlertTemplates';
