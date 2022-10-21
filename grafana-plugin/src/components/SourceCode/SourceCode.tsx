import React, { FC } from 'react';

import { Button, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';
import CopyToClipboard from 'react-copy-to-clipboard';

import { openNotification } from 'utils';

import styles from './SourceCode.module.scss';

const cx = cn.bind(styles);

interface SourceCodeProps {
  noMaxHeight?: boolean;
  showClipboardIconOnly?: boolean;
  showCopyToClipboard?: boolean;
  children?: any;
}

const SourceCode: FC<SourceCodeProps> = ({
  children,
  noMaxHeight = false,
  showClipboardIconOnly = false,
  showCopyToClipboard = true,
}) => {
  const showClipboardCopy = showClipboardIconOnly || showCopyToClipboard;

  return (
    <div className={cx('root')}>
      {showClipboardCopy && (
        <CopyToClipboard
          text={children as string}
          onCopy={() => {
            openNotification('Copied!');
          }}
        >
          {showClipboardIconOnly ? (
            <IconButton className={cx('copyIcon')} size={'lg'} name="copy" data-testid="test__copyIcon" />
          ) : (
            <Button
              className={cx('copyButton')}
              variant="primary"
              size="xs"
              icon="copy"
              data-testid="test__copyIconWithText"
            >
              Copy
            </Button>
          )}
        </CopyToClipboard>
      )}
      <pre
        className={cx('scroller', {
          'scroller--maxHeight': !noMaxHeight,
        })}
      >
        <code>{children}</code>
      </pre>
    </div>
  );
};

export default SourceCode;
