import React from 'react';

import { Button, Stack, useStyles2 } from '@grafana/ui';
import { useCommonStyles } from 'helpers/hooks';
import { observer } from 'mobx-react';

import { WebhookLastEventDetails } from 'components/Webhooks/WebhookLastEventDetails';
import { getWebhookFormStyles } from 'containers/OutgoingWebhookForm/OutgoingWebhookForm';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

interface OutgoingWebhookStatusProps {
  id: ApiSchemas['Webhook']['id'];
  closeDrawer: () => void;
}

export const OutgoingWebhookStatus = observer(({ id, closeDrawer }: OutgoingWebhookStatusProps) => {
  const {
    outgoingWebhookStore: {
      items: { [id]: webhook },
    },
  } = useStore();
  const commonStyles = useCommonStyles();
  const styles = useStyles2(getWebhookFormStyles);

  return (
    <div className={styles.content}>
      <WebhookLastEventDetails webhook={webhook} sourceCodeRootClassName={styles.sourceCodeRoot} />
      <div className={commonStyles.bottomDrawerButtons}>
        <Stack justifyContent="flex-end">
          <Button variant="secondary" onClick={closeDrawer}>
            Close
          </Button>
        </Stack>
      </div>
    </div>
  );
});
