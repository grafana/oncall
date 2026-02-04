import React, { useCallback, useState } from 'react';

import { css } from '@emotion/css';
import { Button, Modal, Field, Input, Stack, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { openErrorNotification } from 'helpers/helpers';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';
import { Controller, FormProvider, useForm } from 'react-hook-form';

import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { useStore } from 'state/useStore';

interface ZoomIntegrationProps {
  disabled?: boolean;
  size?: 'md' | 'lg';
  onUpdate: () => void;
}
export const ZoomIntegrationButton = observer((props: ZoomIntegrationProps) => {
  const { disabled, size = 'md', onUpdate } = props;

  const [showModal, setShowModal] = useState<boolean>(false);

  const onModalCreateCallback = useCallback(() => {
    setShowModal(true);
  }, []);

  const onModalCancelCallback = useCallback(() => {
    setShowModal(false);
  }, []);

  const onModalUpdateCallback = useCallback(() => {
    setShowModal(false);

    onUpdate();
  }, [onUpdate]);

  return (
    <>
      <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
        <Button size={size} variant="primary" icon="plus" disabled={disabled} onClick={onModalCreateCallback}>
          Add Zoom channel
        </Button>
      </WithPermissionControlTooltip>
      {showModal && <ZoomChannelForm onHide={onModalCancelCallback} onUpdate={onModalUpdateCallback} />}
    </>
  );
});

interface ZoomCreationModalProps {
  onHide: () => void;
  onUpdate: () => void;
}

interface FormFields {
  channelId: string;
  channelName: string;
}

const ZoomChannelForm = (props: ZoomCreationModalProps) => {
  const { onHide, onUpdate } = props;
  const store = useStore();

  const formMethods = useForm<FormFields>({
    mode: 'onChange',
  });

  const {
    control,
    watch,
    formState: { errors },
    handleSubmit,
  } = formMethods;

  const channelId = watch('channelId');
  const channelName = watch('channelName');

  const styles = useStyles2(getStyles);

  return (
    <Modal title="Add Zoom Channel" isOpen closeOnEscape={false} onDismiss={onUpdate}>
      <FormProvider {...formMethods}>
        <form onSubmit={handleSubmit(onCreateChannelCallback)}>
          <Stack direction="column">
            {renderChannelIdInput()}
            {renderChannelNameInput()}
            <Stack justifyContent="flex-end">
              <Button variant="secondary" onClick={() => onHide()}>
                Cancel
              </Button>
              <Button type="submit" disabled={!channelId || !channelName} variant="primary">
                Create
              </Button>
            </Stack>
          </Stack>
        </form>
      </FormProvider>
    </Modal>
  );

  function renderChannelIdInput() {
    return (
      <Controller
        name="channelId"
        control={control}
        rules={{ required: 'Channel Id is required' }}
        render={({ field }) => (
          <Field
            label="Zoom Channel ID (JID)"
            invalid={Boolean(errors['channelId'])}
            error={errors['channelId']?.message}
            className={styles.field}
          >
            <Input
              {...field}
              className={styles.channelFormFieldInput}
              maxLength={100}
              placeholder="Enter Zoom Channel JID"
              autoFocus
            />
          </Field>
        )}
      />
    );
  }

  function renderChannelNameInput() {
    return (
      <Controller
        name="channelName"
        control={control}
        rules={{ required: 'Channel Name is required' }}
        render={({ field }) => (
          <Field
            label="Zoom Channel Name"
            invalid={Boolean(errors['channelName'])}
            error={errors['channelName']?.message}
            className={styles.field}
          >
            <Input
              {...field}
              className={styles.channelFormFieldInput}
              maxLength={100}
              placeholder="Enter Zoom Channel Name"
            />
          </Field>
        )}
      />
    );
  }

  async function onCreateChannelCallback() {
    try {
      await store.zoomChannelStore.create({ channel_id: channelId, channel_name: channelName }, true);
      onUpdate();
    } catch (error) {
      openErrorNotification(get(error, 'response.data.detail', 'error creating channel'));
    }
  }
};

const getStyles = () => {
  return {
    channelFormFieldInput: css`
      border-top-right-radius: 0;
      border-bottom-right-radius: 0;
    `,

    field: css`
      flex-grow: 1;
    `,
  };
};
