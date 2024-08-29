import React, { FC, HTMLAttributes, ChangeEvent, useState, useCallback } from 'react';

import { cx } from '@emotion/css';
import { IconButton, Modal, Input, Stack, Button, useStyles2 } from '@grafana/ui';
import CopyToClipboard from 'react-copy-to-clipboard';
import { bem } from 'styles/utils.styles';

import { openNotification } from 'utils/utils';

import { getTextStyles } from './Text.styles';

export type TextType = 'primary' | 'secondary' | 'disabled' | 'link' | 'success' | 'warning' | 'danger';

interface TextProps extends HTMLAttributes<HTMLElement> {
  type?: TextType;
  strong?: boolean;
  underline?: boolean;
  size?: 'xs' | 'small' | 'medium' | 'large';
  display?: 'inline' | 'block' | 'inline-block';
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
  customTag?: 'h6' | 'span';
  withBackground?: boolean;
}

const PLACEHOLDER = '**********';

export const Text: React.FC<TextProps> & { Title: typeof Title } = (props) => {
  const {
    type,
    size = 'medium',
    display = 'inline',
    strong = false,
    underline = false,
    children,
    onClick,
    className,
    wrap = true,
    copyable = false,
    editable = false,
    onTextChange,
    clearBeforeEdit = false,
    hidden = false,
    editModalTitle = 'New value',
    withBackground = false,
    style,
    maxWidth,
    clickable,
    customTag,
    ...rest
  } = props;

  const styles = useStyles2(getTextStyles);

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

  const CustomTag = (customTag || `span`) as unknown as React.ComponentType<any>;

  return (
    <CustomTag
      onClick={onClick}
      className={cx(
        styles.root,
        styles.text,
        { [styles.maxWidth]: Boolean(maxWidth) },
        bem(styles.text, type),
        bem(styles.text, size),
        bem(styles.display, display),
        { [bem(styles.text, `strong`)]: strong },
        { [bem(styles.text, `underline`)]: underline },
        { [bem(styles.text, 'clickable')]: clickable },
        { [styles.noWrap]: !wrap },
        { [styles.withBackground]: withBackground },
        className
      )}
      style={{ ...style, maxWidth }}
      {...rest}
    >
      {hidden ? PLACEHOLDER : children}
      {editable && (
        <IconButton
          onClick={handleEditClick}
          className={styles.iconButton}
          tooltip="Edit"
          tooltipPlacement="top"
          data-emotion="iconButton"
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
            className={styles.iconButton}
            tooltip="Copy to clipboard"
            tooltipPlacement="top"
            data-emotion="iconButton"
            name="copy"
          />
        </CopyToClipboard>
      )}
      {isEditMode && (
        <Modal onDismiss={handleCancelEdit} closeOnEscape isOpen title={editModalTitle}>
          <Stack direction="column">
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
            <Stack justifyContent="flex-end">
              <Button variant="secondary" onClick={handleCancelEdit}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleConfirmEdit}>
                Ok
              </Button>
            </Stack>
          </Stack>
        </Modal>
      )}
    </CustomTag>
  );
};

interface TitleProps extends TextProps {
  level: 1 | 2 | 3 | 4 | 5 | 6;
}

const Title: FC<TitleProps> = (props) => {
  const styles = useStyles2(getTextStyles);

  const { level, className, style, ...restProps } = props;
  // @ts-ignore
  const Tag: keyof JSX.IntrinsicElements = `h${level}`;

  return (
    <Tag className={cx(styles.title, className)} style={style}>
      <Text {...restProps} />
    </Tag>
  );
};

Text.Title = Title;
