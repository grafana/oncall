import React, { FC } from 'react';

import { Button, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';
import CopyToClipboard from 'react-copy-to-clipboard';

import { formatSourceCodeJsonString } from 'utils/string';
import { openNotification } from 'utils/utils';

import styles from './SourceCode.module.scss';

const cx = cn.bind(styles);

interface SourceCodeProps {
  noMaxHeight?: boolean;
  showClipboardIconOnly?: boolean;
  showCopyToClipboard?: boolean;
  children?: string;
  rootClassName?: string;
  preClassName?: string;
  prettifyJsonString?: boolean;
}

export const SourceCode: FC<SourceCodeProps> = ({
  children,
  noMaxHeight = false,
  showClipboardIconOnly = false,
  showCopyToClipboard = true,
  rootClassName,
  preClassName,
  prettifyJsonString,
}) => {
  const showClipboardCopy = showClipboardIconOnly || showCopyToClipboard;

  return (
    <div className={cx('root', rootClassName)}>
      {showClipboardCopy && (
        <CopyToClipboard
          text={children}
          onCopy={() => {
            openNotification('Copied!');
          }}
        >
          {showClipboardIconOnly ? (
            <IconButton
              aria-label="Copy"
              className={cx('copyIcon')}
              size={'lg'}
              name="copy"
              data-testid="test__copyIcon"
            />
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
        className={cx(
          'scroller',
          {
            'scroller--maxHeight': !noMaxHeight,
          },
          preClassName
        )}
      >
        <code>{prettifyJsonString ? formatSourceCodeJsonString(children) : children}</code>
      </pre>
    </div>
  );
};
