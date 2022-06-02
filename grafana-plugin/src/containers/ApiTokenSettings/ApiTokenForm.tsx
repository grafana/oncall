import React, { useCallback, HTMLAttributes, useState } from 'react';

import { Button, Field, HorizontalGroup, Input, Modal, VerticalGroup } from '@grafana/ui';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';

import { ApiToken } from 'models/api_token/api_token.types';
import { useStore } from 'state/useStore';
import { openErrorNotification, openNotification } from 'utils';

interface TokenCreationModalProps extends HTMLAttributes<HTMLElement> {
  visible: boolean;
  onHide: () => void;
  onUpdate: () => void;
}

const ApiTokenForm = observer((props: TokenCreationModalProps) => {
  const { visible, onHide = () => {}, onUpdate = () => {} } = props;
  const [name, setName] = useState('');
  const [token, setToken] = useState('');

  const store = useStore();

  const onCreateTokenCallback = useCallback(() => {
    store.apiTokenStore
      .create({ name })
      .then((data: ApiToken) => {
        setToken(data.token);
        onUpdate();
      })
      .catch((error) => openErrorNotification(get(error, 'response.data.detail', 'error creating token')));
  }, [name]);

  const handleNameChange = useCallback((event) => {
    setName(event.target.value);
  }, []);

  return (
    <Modal isOpen closeOnEscape={false} title={token ? 'Your new API Token' : 'Create API Token'} onDismiss={onHide}>
      <VerticalGroup>
        <Input maxLength={50} onChange={handleNameChange} autoFocus placeholder="Enter token name" />
        {token && (
          <>
            <Input value={token} disabled />
          </>
        )}
        <HorizontalGroup>
          {token && (
            <CopyToClipboard
              text={token}
              onCopy={() => {
                openNotification('Token copied');
              }}
            >
              <Button>Copy Token</Button>
            </CopyToClipboard>
          )}
          <Button disabled={!!token || !name} variant="primary" onClick={onCreateTokenCallback}>
            Create
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );
});

export default ApiTokenForm;
