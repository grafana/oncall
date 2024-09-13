import React, { HTMLAttributes, useState } from 'react';

import { Button, Field, Input, Label, Modal, Stack, useStyles2 } from '@grafana/ui';
import { openNotification, openErrorNotification } from 'helpers/helpers';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';
import { Controller, FormProvider, useForm } from 'react-hook-form';

import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { SourceCode } from 'components/SourceCode/SourceCode';
import { useStore } from 'state/useStore';

import { getApiTokenFormStyles } from './ApiTokenForm.styles';

interface TokenCreationModalProps extends HTMLAttributes<HTMLElement> {
  visible: boolean;
  onHide: () => void;
  onUpdate: () => void;
}

interface FormFields {
  name: string;
}

export const ApiTokenForm = observer((props: TokenCreationModalProps) => {
  const { onHide = () => {}, onUpdate = () => {} } = props;
  const [token, setToken] = useState('');
  const styles = useStyles2(getApiTokenFormStyles);

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

  const name = watch('name');

  return (
    <Modal isOpen closeOnEscape={false} title={token ? 'Your new API Token' : 'Create API Token'} onDismiss={onHide}>
      <FormProvider {...formMethods}>
        <form onSubmit={handleSubmit(onCreateTokenCallback)}>
          <Stack direction="column">
            <Label>Token Name</Label>
            <div className={styles.tokenInputContainer}>
              {renderTokenInput()}
              {renderCopyToClipboard()}
            </div>

            {renderCurlExample()}

            <Stack justifyContent="flex-end">
              <Button variant="secondary" onClick={() => onHide()}>
                {token ? 'Close' : 'Cancel'}
              </Button>

              <RenderConditionally shouldRender={!token}>
                <Button type="submit" disabled={!name} variant="primary">
                  Create Token
                </Button>
              </RenderConditionally>
            </Stack>
          </Stack>
        </form>
      </FormProvider>
    </Modal>
  );

  function renderTokenInput() {
    return (
      <Controller
        name="name"
        control={control}
        rules={{ required: 'Token name is required' }}
        render={({ field }) => (
          <Field invalid={Boolean(errors['name'])} error={errors['name']?.message} className={styles.field}>
            <>
              {token ? (
                <Input {...field} disabled={!!token} className={styles.tokenInput} />
              ) : (
                <Input
                  {...field}
                  className={styles.tokenInput}
                  maxLength={50}
                  placeholder="Enter token name"
                  autoFocus
                />
              )}
            </>
          </Field>
        )}
      />
    );
  }

  function renderCopyToClipboard() {
    if (!token) {
      return null;
    }
    return (
      <CopyToClipboard text={token} onCopy={() => openNotification('Token copied')}>
        <Button className={styles.tokenCopyButton}>Copy Token</Button>
      </CopyToClipboard>
    );
  }

  function renderCurlExample() {
    if (!token) {
      return null;
    }
    return (
      <Stack direction="column">
        <Label>Curl command example</Label>
        <SourceCode noMinHeight showClipboardIconOnly>
          {getCurlExample(token, store.pluginStore.apiUrlFromStatus)}
        </SourceCode>
      </Stack>
    );
  }

  async function onCreateTokenCallback() {
    try {
      const data = await store.apiTokenStore.create({ name });
      setToken(data.token);
      onUpdate();
    } catch (error) {
      openErrorNotification(get(error, 'response.data.detail', 'error creating token'));
    }
  }
});

function getCurlExample(token: string, onCallApiUrl: string) {
  return `curl -H "Authorization: ${token}" ${onCallApiUrl}/api/v1/integrations`;
}
