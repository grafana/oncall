import React, { useCallback, useState } from 'react';

import { Button, Drawer, Input, Modal } from '@grafana/ui';
import cn from 'classnames/bind';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';
import Emoji from 'react-emoji-render';

import GForm from 'components/GForm/GForm';
import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import Text from 'components/Text/Text';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { useStore } from 'state/useStore';
import { UserAction } from 'state/userAction';
import { openErrorNotification } from 'utils';

import { form } from './OutgoingWebhookForm.config';

import styles from 'containers/OutgoingWebhookForm/OutgoingWebhookForm.module.css';

const cx = cn.bind(styles);

interface OutgoingWebhookFormProps {
  id: OutgoingWebhook['id'] | 'new';
  onHide: () => void;
  onUpdate: () => void;
}

const OutgoingWebhookForm = observer((props: OutgoingWebhookFormProps) => {
  const { id, onUpdate, onHide } = props;

  const store = useStore();

  const { outgoingWebhookStore } = store;

  const data = id === 'new' ? {} : outgoingWebhookStore.items[id];

  const handleSubmit = useCallback(
    (data: Partial<OutgoingWebhook>) => {
      (id === 'new' ? outgoingWebhookStore.create(data) : outgoingWebhookStore.update(id, data)).then(() => {
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
      <div className={cx('content')}>
        <GForm form={form} data={data} onSubmit={handleSubmit} />
        <WithPermissionControl userAction={UserAction.UpdateCustomActions}>
          <Button form={form.name} type="submit">
            {id === 'new' ? 'Create' : 'Update'} Webhook
          </Button>
        </WithPermissionControl>
      </div>
    </Drawer>
  );
});

export default OutgoingWebhookForm;
