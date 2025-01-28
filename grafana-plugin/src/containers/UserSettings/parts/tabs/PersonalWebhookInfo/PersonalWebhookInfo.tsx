import React from 'react';

import { css } from '@emotion/css';
import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';

export const PersonalWebhookInfo = observer(() => {
  return (
    <>
      <Text.Title
        level={2}
        className={css`
          margin-bottom: 24px;
        `}
      >
        Setup Personal Webhook
      </Text.Title>
      {/* allow selecting a personal webhook + setting additional metadata as context */}
    </>
  );
});
