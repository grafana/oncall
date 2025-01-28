import React from 'react';

import { InlineField, Input, Stack } from '@grafana/ui';
import { StackSize } from 'helpers/consts';
import { observer } from 'mobx-react';

import { UserSettingsTab } from 'containers/UserSettings/UserSettings.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

interface PersonalWebhookConnectorProps {
  id: ApiSchemas['User']['pk'];
  onTabChange: (tab: UserSettingsTab) => void;
}

export const PersonalWebhookConnector = observer((props: PersonalWebhookConnectorProps) => {
  const { id } = props;

  const store = useStore();
  const { userStore } = store;

  const storeUser = userStore.items[id];
  const isCurrentUser = id === store.userStore.currentUserPk;

  return (
    <div>
        <InlineField label="Webhook" labelWidth={12} disabled={!isCurrentUser}>
          <Stack gap={StackSize.xs}>
            <Input disabled={true} value={(storeUser.messaging_backends.WEBHOOK?.name as string) || '—'} />
          </Stack>
        </InlineField>
    </div>
  );
});
