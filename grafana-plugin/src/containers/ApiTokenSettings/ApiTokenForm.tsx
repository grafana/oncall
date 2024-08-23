import React, { HTMLAttributes, useState } from 'react';

import { Button, Field, HorizontalGroup, Input, Label, Modal, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';
import { Controller, FormProvider, useForm } from 'react-hook-form';

import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { SourceCode } from 'components/SourceCode/SourceCode';
import { useStore } from 'state/useStore';
import { openErrorNotification, openNotification } from 'utils/utils';

import styles from './ApiTokenForm.module.css';

const cx = cn.bind(styles);

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
          <VerticalGroup>
            <Label>Token Name</Label>
            <div className={cx('token__inputContainer')}>
              {renderTokenInput()}
              {renderCopyToClipboard()}
            </div>

            {renderCurlExample()}

            <HorizontalGroup justify="flex-end">
              <Button variant="secondary" onClick={() => onHide()}>
                {token ? 'Close' : 'Cancel'}
              </Button>

              <RenderConditionally shouldRender={!token}>
                <Button type="submit" disabled={!name} variant="primary">
                  Create Token
                </Button>
              </RenderConditionally>
            </HorizontalGroup>
          </VerticalGroup>
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
          <Field invalid={Boolean(errors['name'])} error={errors['name']?.message} className={cx('field')}>
            <>
              {token ? (
                <Input {...field} disabled={!!token} className={cx('token__input')} />
              ) : (
                <Input
                  {...field}
                  className={cx('token__input')}
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
        <Button className={cx('token__copyButton')}>Copy Token</Button>
      </CopyToClipboard>
    );
  }

  function renderCurlExample() {
    if (!token) {
      return null;
    }
    return (
      <VerticalGroup>
        <Label>Curl command example</Label>
        <SourceCode noMinHeight showClipboardIconOnly>
          {getCurlExample(token, store.pluginStore.apiUrlFromStatus)}
        </SourceCode>
      </VerticalGroup>
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

function getCurlExample(token, onCallApiUrl) {
  return `curl -H "Authorization: ${token}" ${onCallApiUrl}/api/v1/integrations`;
}
