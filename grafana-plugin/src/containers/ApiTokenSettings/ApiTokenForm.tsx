import React, { useCallback, HTMLAttributes, useState } from 'react';

import { Button, HorizontalGroup, Input, Label, Modal, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';
import CopyToClipboard from 'react-copy-to-clipboard';

import SourceCode from 'components/SourceCode/SourceCode';
import { ApiToken } from 'models/api_token/api_token.types';
import { useStore } from 'state/useStore';
import { openErrorNotification, openNotification } from 'utils';

import styles from './ApiTokenForm.module.css';

const cx = cn.bind(styles);

interface TokenCreationModalProps extends HTMLAttributes<HTMLElement> {
  visible: boolean;
  onHide: () => void;
  onUpdate: () => void;
}

const ApiTokenForm = observer((props: TokenCreationModalProps) => {
  const { onHide = () => {}, onUpdate = () => {} } = props;
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
          {!token && (
            <Button disabled={!!token || !name} variant="primary" onClick={onCreateTokenCallback}>
              Create Token
            </Button>
          )}
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );

  function renderTokenInput() {
    return token ? (
      <Input value={token} disabled={!!token} className={cx('token__input')} />
    ) : (
      <Input
        className={cx('token__input')}
        maxLength={50}
        onChange={handleNameChange}
        placeholder="Enter token name"
        autoFocus
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
        <SourceCode showClipboardIconOnly>{getCurlExample(token, store.onCallApiUrl)}</SourceCode>
      </VerticalGroup>
    );
  }
});

function getCurlExample(token, onCallApiUrl) {
  return `curl -H "Authorization: ${token}" ${onCallApiUrl}/api/v1/integrations`;
}

export default ApiTokenForm;
