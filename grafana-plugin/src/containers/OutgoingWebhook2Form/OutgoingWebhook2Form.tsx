import React, { useCallback } from 'react';

import { Button, Drawer } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import GForm from 'components/GForm/GForm';
import Text from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { OutgoingWebhook2 } from 'models/outgoing_webhook_2/outgoing_webhook_2.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

import { form } from './OutgoingWebhook2Form.config';

import styles from 'containers/OutgoingWebhook2Form/OutgoingWebhook2Form.module.css';

const cx = cn.bind(styles);

interface OutgoingWebhook2FormProps {
  id: OutgoingWebhook2['id'] | 'new';
  onHide: () => void;
  onUpdate: () => void;
}

const OutgoingWebhook2Form = observer((props: OutgoingWebhook2FormProps) => {
  const { id, onUpdate, onHide } = props;

  const store = useStore();

  const { outgoingWebhook2Store } = store;

  const data = id === 'new' ? { is_webhook_enabled: true, is_legacy: false } : outgoingWebhook2Store.items[id];

  const handleSubmit = useCallback(
    (data: Partial<OutgoingWebhook2>) => {
      (id === 'new' ? outgoingWebhook2Store.create(data) : outgoingWebhook2Store.update(id, data)).then(() => {
        onHide();

        onUpdate();
      });
    },
    [id]
  );

  return (
    <Drawer
      scrollableContent
      title={
        <Text.Title className={cx('title')} level={4}>
          {id === 'new' ? 'Create' : 'Edit'} Outgoing Webhook
        </Text.Title>
      }
      onClose={onHide}
      closeOnMaskClick
    >
      <div className={cx('content')} data-testid="test__outgoingWebhook2EditForm">
        <GForm form={form} data={data} onSubmit={handleSubmit} />
        <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
          <Button form={form.name} type="submit" disabled={data.is_legacy}>
            {id === 'new' ? 'Create' : 'Update'} Webhook
          </Button>
        </WithPermissionControlTooltip>
      </div>
      {data.is_legacy ? (
        <div className={cx('content')}>
          <Text type="secondary">Legacy migrated webhooks are not editable.</Text>
        </div>
      ) : (
        ''
      )}
    </Drawer>
  );
});

export default OutgoingWebhook2Form;
