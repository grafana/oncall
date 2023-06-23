import React, { useState } from 'react';

import { HorizontalGroup, IconButton, Input } from '@grafana/ui';
import cn from 'classnames/bind';
import CopyToClipboard from 'react-copy-to-clipboard';

import { openNotification } from 'utils';

import styles from './IntegrationInputField.module.scss';

interface IntegrationInputFieldProps {
  value: string;
  isMasked?: boolean;
  showEye?: boolean;
  showCopy?: boolean;
  showExternal?: boolean;
  className?: string;
}

const cx = cn.bind(styles);

const IntegrationInputField: React.FC<IntegrationInputFieldProps> = ({
  isMasked = true,
  value,
  showEye = true,
  showCopy = true,
  showExternal = true,
  className,
}) => {
  const [isInputMasked, setIsMasked] = useState(isMasked);

  return (
    <div className={cx('root', { [className]: !!className })}>
      <div className={cx('input-container')}>{renderInputField()}</div>

      <div className={cx('icons')}>
        <HorizontalGroup spacing={'xs'}>
          {showEye && <IconButton name={'eye'} size={'xs'} onClick={onInputReveal} />}
          {showCopy && (
            <CopyToClipboard text={value} onCopy={onCopy}>
              <IconButton name={'copy'} size={'xs'} />
            </CopyToClipboard>
          )}
          {showExternal && <IconButton name={'external-link-alt'} size={'xs'} onClick={onOpen} />}
        </HorizontalGroup>
      </div>
    </div>
  );

  function renderInputField() {
    return <Input className={cx('input')} value={isInputMasked ? value?.replace(/./g, '*') : value} disabled />;
  }

  function onInputReveal() {
    setIsMasked(!isInputMasked);
  }

  function onCopy() {
    openNotification("Integration's HTTP Endpoint is copied");
  }

  function onOpen() {
    window.open(value, '_blank');
  }
};

export default IntegrationInputField;
