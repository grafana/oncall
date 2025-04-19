import { clone } from 'lodash-es'

import { MONACO_INPUT_HEIGHT_SMALL, MONACO_INPUT_HEIGHT_TALL } from 'pages/integration/IntegrationCommon.config';
import { AppFeature } from 'state/features';

import { TemplateBlock, commonTemplatesToRender } from './IntegrationCommonTemplatesList.config';

const additionalTemplatesToRender: TemplateBlock[] = [
  {
    name: 'MS Teams',
    contents: [
      {
        name: 'msteams_title_template',
        label: 'Title',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
      {
        name: 'msteams_message_template',
        label: 'Message',
        height: MONACO_INPUT_HEIGHT_TALL,
      },
      {
        name: 'msteams_image_url_template',
        label: 'Image',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
    ],
  },
  {
    name: 'Mattermost',
    contents: [
      {
        name: 'mattermost_title_template',
        label: 'Title',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
      {
        name: 'mattermost_message_template',
        label: 'Message',
        height: MONACO_INPUT_HEIGHT_TALL,
      },
      {
        name: 'mattermost_image_url_template',
        label: 'Image',
        height: MONACO_INPUT_HEIGHT_SMALL,
      },
    ],
  }
];

export const getTemplatesToRender = (features?: Record<string, boolean>) => {
  const templatesToRender = clone(commonTemplatesToRender)
  if (features?.[AppFeature.MsTeams]) {
    templatesToRender.push(additionalTemplatesToRender[0]);
  }
  if (features?.[AppFeature.Mattermost]) {
    templatesToRender.push(additionalTemplatesToRender[1])
  }
  return templatesToRender;
};
