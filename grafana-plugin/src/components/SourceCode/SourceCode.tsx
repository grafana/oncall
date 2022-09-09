import React, { FC } from 'react';

import { Button } from '@grafana/ui';
import cn from 'classnames/bind';
import CopyToClipboard from 'react-copy-to-clipboard';

import { openNotification } from 'utils';

import styles from './SourceCode.module.css';

const cx = cn.bind(styles);

interface SourceCodeProps {
  noMaxHeight?: boolean;
  showCopyToClipboard?: boolean;
  children?: any;
}

const SourceCode: FC<SourceCodeProps> = (props) => {
  const { children, noMaxHeight = false, showCopyToClipboard = true } = props;

  return (
    <div className={cx('root')}>
      {showCopyToClipboard && (
        <CopyToClipboard
          text={children as string}
          onCopy={() => {
            openNotification('Copied!');
          }}
        >
          <Button className={cx('button')} variant="primary" icon="copy">
            Copy
          </Button>
        </CopyToClipboard>
      )}
      <pre
        className={cx('scroller', {
          'scroller_max-height': !noMaxHeight,
        })}
      >
        <code>{children}</code>
      </pre>
    </div>
  );
};

export default SourceCode;
