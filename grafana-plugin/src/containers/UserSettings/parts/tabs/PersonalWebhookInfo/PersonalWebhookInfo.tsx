import React from 'react';

import { Stack } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { Text } from 'components/Text/Text';

export const PersonalWebhookInfo = observer(() => {
  return (
    <>
      {/* allow selecting a personal webhook + setting additional metadata as context */}
      <Stack direction="column" alignItems="flex-start" gap={StackSize.lg}>
        <Block bordered withBackground>
          <Stack direction="column" alignItems="center">
            <Text>Choose a personal notification webhook</Text>
            <br />
            <Text>Set your user specific context data</Text>
            <br />
            <Text>Display current settings</Text>
          </Stack>
        </Block>
      </Stack>
    </>
  );
});
