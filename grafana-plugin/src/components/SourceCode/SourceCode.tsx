import React, { FC } from 'react';

import { Button } from '@grafana/ui';
import cn from 'classnames/bind';
import CopyToClipboard from 'react-copy-to-clipboard';

import { openNotification } from 'utils';

import styles from './SourceCode.module.scss';

const cx = cn.bind(styles);

interface SourceCodeProps {
  noMaxHeight?: boolean;
  showCopyToClipboard?: boolean;
  isButtonTopPositioned?: boolean;
  children?: any;
}

const SourceCode: FC<SourceCodeProps> = (props) => {
  const { children, isButtonTopPositioned = false, noMaxHeight = false, showCopyToClipboard = true } = props;

  return (
    <div className={cx('root')}>
      {showCopyToClipboard && (
        <CopyToClipboard
          text={children as string}
          onCopy={() => {
            openNotification('Copied!');
          }}
        >
          <Button
            className={cx('button', {
              'button--top': isButtonTopPositioned,
            })}
            variant="primary"
            icon="copy"
          >
            Copy
          </Button>
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
