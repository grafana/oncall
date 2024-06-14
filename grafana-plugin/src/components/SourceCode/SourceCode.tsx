import React, { FC } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Button, IconButton, useStyles2 } from '@grafana/ui';
import CopyToClipboard from 'react-copy-to-clipboard';
import { bem } from 'styles/utils.styles';

import { formatSourceCodeJsonString } from 'utils/string';
import { openNotification } from 'utils/utils';

interface SourceCodeProps {
  noMaxHeight?: boolean;
  noMinHeight?: boolean;
  noMarginBottom?: boolean;
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
  noMinHeight = false,
  showClipboardIconOnly = false,
  showCopyToClipboard = true,
  rootClassName,
  preClassName,
  prettifyJsonString,
}) => {
  const showClipboardCopy = showClipboardIconOnly || showCopyToClipboard;
  const styles = useStyles2(getStyles);

  return (
    <div
      className={cx(
        styles.root,
        {
          [bem(styles.root, 'noMinHeight')]: noMinHeight,
        },
        rootClassName
      )}
    >
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
              className={styles.copyIcon}
              size={'lg'}
              name="copy"
              data-emotion="copyIcon"
              data-testid="test__copyIcon"
            />
          ) : (
            <Button
              className={styles.copyIcon}
              variant="primary"
              size="xs"
              icon="copy"
              data-testid="test__copyIconWithText"
              data-emotion="copyIcon"
            >
              Copy
            </Button>
          )}
        </CopyToClipboard>
      )}
      <pre
        className={cx(
          styles.scroller,
          {
            [bem(styles.scroller, 'maxHeight')]: !noMaxHeight,
          },
          preClassName
        )}
      >
        <code>{prettifyJsonString ? formatSourceCodeJsonString(children) : children}</code>
      </pre>
    </div>
  );
};

const getStyles = (_theme: GrafanaTheme2) => {
  return {
    root: css`
      position: relative;
      width: 100%;

      &:hover [data-emotion='copyIcon'] {
        opacity: 1;
      }

      pre {
        min-height: 200px;
      }

      &--noMinHeight pre {
        min-height: unset;
      }
    `,
    copyIcon: css`
      position: absolute;
      top: 15px;
      right: 15px;
      transition: opacity 0.2s ease;
      opacity: 0;
    `,
    scroller: css`
      overflow-y: auto;
      border-radius: 2px;
      padding: 12px 60px 12px 20px;

      &--maxHeight {
        max-height: 400px;
      }
    `,
  };
};
