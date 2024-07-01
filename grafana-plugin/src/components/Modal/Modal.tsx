import React, { FC, PropsWithChildren } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { useStyles2 } from '@grafana/ui';
import ReactModal from 'react-modal';

ReactModal.setAppElement('#reactRoot');

export interface ModalProps {
  title?: string | JSX.Element;
  className?: string;
  contentClassName?: string;
  closeOnEscape?: boolean;
  closeOnBackdropClick?: boolean;
  onDismiss?: () => void;
  width: string;
  contentElement?: (props, children: React.ReactNode) => React.ReactNode;
  isOpen: boolean;
  top?: string;
}

export const Modal: FC<PropsWithChildren<ModalProps>> = (props) => {
  const styles = useStyles2(getStyles);
  const { title, children, onDismiss, width = '600px', contentElement, isOpen = true, top, className } = props;

  return (
    <ReactModal
      shouldCloseOnOverlayClick={false}
      style={{
        overlay: {},
        content: {
          width,
          top,
        },
      }}
      isOpen={isOpen}
      onAfterOpen={() => {}}
      onRequestClose={onDismiss}
      contentLabel={title}
      className={cx(styles.root, className)}
      overlayElement={(_props, contentElement) => contentElement} // render without overlay to allow body scroll
      contentElement={contentElement}
    >
      {children}
    </ReactModal>
  );
};

const getStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      position: fixed;
      width: 750px;
      max-width: 100%;
      left: 0;
      right: 0;
      margin-left: auto;
      margin-right: auto;
      top: 10%;
      max-height: 90%;
      display: flex;
      flex-direction: column;
      border-image: initial;
      outline: none;
      padding: 15px;
      background: ${theme.colors.background.primary};
      border: 1px solid ${theme.colors.border.weak};
      box-shadow: var(--shadows-z3);
      border-radius: 2px;
      z-index: 10;
    `,
  };
};
