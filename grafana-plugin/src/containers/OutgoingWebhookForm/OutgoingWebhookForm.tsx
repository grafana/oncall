import React, { useCallback } from 'react';

import { Button, Drawer, HorizontalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import GForm from 'components/GForm/GForm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

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

  const { outgoingWebhookStore, userStore } = store;
  const user = userStore.currentUser;

  const data = id === 'new' ? { team: user.current_team } : outgoingWebhookStore.items[id];

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
      title={id === 'new' ? 'Create Outgoing Webhook' : 'Edit Outgoing Webhook'}
      onClose={onHide}
      closeOnMaskClick={false}
    >
      <div className={cx('content')} data-testid="test__outgoingWebhookEditForm">
        <GForm form={form} data={data} onSubmit={handleSubmit} />
        <HorizontalGroup justify="flex-end">
          <Button variant="secondary" onClick={onHide}>
            Cancel
          </Button>
          <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
            <Button form={form.name} type="submit">
              {id === 'new' ? 'Create' : 'Update'} Webhook
            </Button>
          </WithPermissionControlTooltip>
        </HorizontalGroup>
      </div>
    </Drawer>
  );
});

export default OutgoingWebhookForm;
