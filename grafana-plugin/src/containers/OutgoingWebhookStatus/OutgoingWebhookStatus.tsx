import React from 'react';

import { Button, Stack } from '@grafana/ui';
import cn from 'classnames/bind';
import { useCommonStyles } from 'helpers/hooks';
import { observer } from 'mobx-react';

import { WebhookLastEventDetails } from 'components/Webhooks/WebhookLastEventDetails';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

import styles from 'containers/OutgoingWebhookForm/OutgoingWebhookForm.module.css';

const cx = cn.bind(styles);

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

  return (
    <div className={cx('content')}>
      <WebhookLastEventDetails webhook={webhook} sourceCodeRootClassName={cx('sourceCodeRoot')} />
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
