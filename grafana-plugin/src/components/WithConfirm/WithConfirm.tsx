import React, { FC, ReactElement, useCallback, useState } from 'react';

import { ConfirmModal } from '@grafana/ui';
import cn from 'classnames/bind';

import styles from './WithConfirm.module.css';

interface WithConfirmProps {
  children: ReactElement;
  title?: string;
  body?: React.ReactNode;
  confirmText?: string;
  disabled?: boolean;
}

const cx = cn.bind(styles);

const WithConfirm = (props: WithConfirmProps) => {
  const { children, title = 'Are you sure to delete?', body, confirmText = 'Delete', disabled } = props;

  const [showConfirmation, setShowConfirmation] = useState<boolean>(false);

  const onClickCallback = useCallback((event) => {
    event.stopPropagation();

    setShowConfirmation(true);
  }, []);

  const onConfirmCallback = useCallback(() => {
    if (children.props.onClick) {
      children.props.onClick();
    }

    setShowConfirmation(false);
  }, [children]);

  return (
    <>
      {showConfirmation && (
        <ConfirmModal
          isOpen
          title={title}
          confirmText={confirmText}
          dismissText="Cancel"
          onConfirm={onConfirmCallback}
          body={body}
          onDismiss={() => {
            setShowConfirmation(false);
          }}
        />
      )}
      {React.cloneElement(children, {
        disabled: children.props.disabled || disabled,
        onClick: onClickCallback,
      })}
    </>
  );
};

export default WithConfirm;
