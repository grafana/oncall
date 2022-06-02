import React, { FC, HTMLAttributes, ChangeEvent, useState, useCallback } from 'react';

import { IconButton, Modal, Field, Input, HorizontalGroup, Button, Icon, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import CopyToClipboard from 'react-copy-to-clipboard';

import { TimelineProps } from 'components/Timeline/Timeline';
import { TimelineItemProps } from 'components/Timeline/TimelineItem';
import { useStore } from 'state/useStore';
import { openNotification } from 'utils';

import styles from './Text.module.css';

interface TextProps extends HTMLAttributes<HTMLElement> {
  type?: 'primary' | 'secondary' | 'disabled' | 'link' | 'success' | 'warning';
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
}

interface TextType extends React.FC<TextProps> {
  Title: React.FC<TitleProps>;
}

const PLACEHOLDER = '**********';

const cx = cn.bind(styles);

const Text: TextType = (props) => {
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
  }, [value]);

  const handleInputChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value);
  }, []);

  return (
    <span
      onClick={onClick}
      className={cx('root', className, {
        [`type_${type}`]: true,
        [`size_${size}`]: true,
        strong,
        underline,
        keyboard,
        'no-wrap': !wrap,
      })}
    >
      {hidden ? PLACEHOLDER : children}
      {editable && (
        <IconButton
          onClick={handleEditClick}
          variant="primary"
          className={cx('icon-button')}
          tooltip="Edit"
          tooltipPlacement="top"
          name="edit"
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
        <Modal onDismiss={handleCancelEdit} closeOnEscape isOpen title="New value">
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
  const { level, className, ...restProps } = props;
  // @ts-ignore
  const Tag: keyof JSX.IntrinsicElements = `h${level}`;

  return (
    <Tag className={cx('title', className)}>
      <Text {...restProps} />
    </Tag>
  );
};

Text.Title = Title;

export default Text;
