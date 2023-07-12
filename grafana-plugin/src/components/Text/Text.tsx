import React, { FC, HTMLAttributes, ChangeEvent, useState, useCallback } from 'react';

import { IconButton, Modal, Input, HorizontalGroup, Button, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import CopyToClipboard from 'react-copy-to-clipboard';

import { openNotification } from 'utils';

import styles from './Text.module.scss';

export type TextType = 'primary' | 'secondary' | 'disabled' | 'link' | 'success' | 'warning' | 'danger';

interface TextProps extends HTMLAttributes<HTMLElement> {
  type?: TextType;
  strong?: boolean;
  underline?: boolean;
  size?: 'small' | 'medium' | 'large';
  keyboard?: boolean;
  className?: string;
  wrap?: boolean;
  copyable?: boolean;
  editable?: boolean;
  onTextChange?: (value: string) => void;
  clearBeforeEdit?: boolean;
  hidden?: boolean;
  editModalTitle?: string;
  maxWidth?: string;
  clickable?: boolean;
}

interface TextInterface extends React.FC<TextProps> {
  Title: React.FC<TitleProps>;
}

const PLACEHOLDER = '**********';

const cx = cn.bind(styles);

const Text: TextInterface = (props) => {
  const {
    type,
    size = 'medium',
    strong = false,
    underline = false,
    children,
    onClick,
    keyboard = false,
    className,
    wrap = true,
    copyable = false,
    editable = false,
    onTextChange,
    clearBeforeEdit = false,
    hidden = false,
    editModalTitle = 'New value',
    style,
    maxWidth,
    clickable,
    ...rest
  } = props;

  const [isEditMode, setIsEditMode] = useState<boolean>(false);
  const [value, setValue] = useState<string | undefined>();

  const handleEditClick = useCallback(() => {
    setValue(clearBeforeEdit || hidden ? '' : (children as string));

    setIsEditMode(true);
  }, [clearBeforeEdit, hidden, children]);

  const handleCancelEdit = useCallback(() => {
    setIsEditMode(false);
  }, []);

  const handleConfirmEdit = useCallback(() => {
    setIsEditMode(false);
    onTextChange(value);
  }, [value, onTextChange]);

  const handleInputChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value);
  }, []);

  return (
    <span
      onClick={onClick}
      className={cx(
        'root',
        'text',
        {
          'with-maxWidth': Boolean(maxWidth),
          [`text--${type}`]: true,
          [`text--${size}`]: true,
          'text--strong': strong,
          'text--underline': underline,
          'text--clickable': clickable,
          'no-wrap': !wrap,
          keyboard,
        },
        className
      )}
      style={{ ...style, maxWidth }}
      {...rest}
    >
      {hidden ? PLACEHOLDER : children}
      {editable && (
        <IconButton
          onClick={handleEditClick}
          className={cx('icon-button')}
          tooltip="Edit"
          tooltipPlacement="top"
          name="pen"
        />
      )}
      {copyable && (
        <CopyToClipboard
          text={children as string}
          onCopy={() => {
            openNotification('Text copied');
          }}
        >
          <IconButton
            variant="primary"
            className={cx('icon-button')}
            tooltip="Copy to clipboard"
            tooltipPlacement="top"
            name="copy"
          />
        </CopyToClipboard>
      )}
      {isEditMode && (
        <Modal onDismiss={handleCancelEdit} closeOnEscape isOpen title={editModalTitle}>
          <VerticalGroup>
            <Input
              autoFocus
              ref={(node) => {
                if (node) {
                  node.focus();
                }
              }}
              value={value}
              onChange={handleInputChange}
            />
            <HorizontalGroup justify="flex-end">
              <Button variant="secondary" onClick={handleCancelEdit}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleConfirmEdit}>
                Ok
              </Button>
            </HorizontalGroup>
          </VerticalGroup>
        </Modal>
      )}
    </span>
  );
};

interface TitleProps extends TextProps {
  level: 1 | 2 | 3 | 4 | 5 | 6;
}

const Title: FC<TitleProps> = (props) => {
  const { level, className, style, ...restProps } = props;
  // @ts-ignore
  const Tag: keyof JSX.IntrinsicElements = `h${level}`;

  return (
    <Tag className={cx('title', className)} style={style}>
      <Text {...restProps} />
    </Tag>
  );
};

Text.Title = Title;

export default Text;
