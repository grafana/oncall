import React, { useState } from 'react';

import { HorizontalGroup, IconButton, Input } from '@grafana/ui';
import cn from 'classnames/bind';
import CopyToClipboard from 'react-copy-to-clipboard';

import { openNotification } from 'utils';

import styles from './IntegrationMaskedInputField.module.scss';

interface IntegrationMaskedInputFieldProps {
  value: string;
}

const cx = cn.bind(styles);

const IntegrationMaskedInputField: React.FC<IntegrationMaskedInputFieldProps> = ({ value }) => {
  const [isMasked, setIsMasked] = useState(true);

  return (
    <div className={cx('root')}>
      <div className={cx('input-container')}>{renderInputField()}</div>

      <div className={cx('icons')}>
        <HorizontalGroup spacing={'xs'}>
          <IconButton name={'eye'} size={'xs'} onClick={onInputReveal} />
          <CopyToClipboard text={value} onCopy={onCopy}>
            <IconButton name={'copy'} size={'xs'} />
          </CopyToClipboard>
          <IconButton name={'external-link-alt'} size={'xs'} onClick={onOpen} />
        </HorizontalGroup>
      </div>
    </div>
  );

  function renderInputField() {
    return <Input className={cx('input')} value={isMasked ? value.replace(/./g, '*') : value} disabled />;
  }

  function onInputReveal() {
    setIsMasked(!isMasked);
  }

  function onCopy() {
    openNotification("Integration's HTTP Endpoint is copied!");
  }

  function onOpen() {
    window.open(value, '_blank');
  }
};

export default IntegrationMaskedInputField;
