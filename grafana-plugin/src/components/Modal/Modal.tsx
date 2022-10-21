import React, { FC, PropsWithChildren } from 'react';

import cn from 'classnames/bind';
import ReactModal from 'react-modal';

ReactModal.setAppElement('#reactRoot');

import styles from './Modal.module.css';

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
}

const cx = cn.bind(styles);

const Modal: FC<PropsWithChildren<ModalProps>> = ({
  title,
  children,
  onDismiss,
  width = '600px',
  contentElement,
  isOpen = true,
}) => (
  <ReactModal
    shouldCloseOnOverlayClick={false}
    style={{
      overlay: {},
      content: {
        width,
      },
    }}
    isOpen={isOpen}
    onAfterOpen={() => {}}
    onRequestClose={onDismiss}
    contentLabel={title}
    className={cx('root')}
    overlayClassName={cx('overlay')}
    overlayElement={(_props, contentElement) => contentElement} // render without overlay to allow body scroll
    contentElement={contentElement}
  >
    {children}
  </ReactModal>
);

export default Modal;
