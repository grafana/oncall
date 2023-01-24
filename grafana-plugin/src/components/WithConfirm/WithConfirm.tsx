import React, { ReactElement, useCallback, useState } from 'react';

import { ConfirmModal, ConfirmModalProps } from '@grafana/ui';

type WithConfirmProps = Partial<ConfirmModalProps> & {
  children: ReactElement;
  disabled?: boolean;
};

const WithConfirm: React.FC<WithConfirmProps> = ({
  title = 'Are you sure to delete?',
  confirmText = 'Delete',
  body,
  description,
  confirmationText,
  children,
  disabled,
}) => {
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
          description={description}
          confirmationText={confirmationText}
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
