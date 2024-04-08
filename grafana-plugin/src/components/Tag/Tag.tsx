import React, { FC } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { useStyles2 } from '@grafana/ui';
import cn from 'classnames/bind';

import { bem } from 'utils/utils';

import styles from 'components/Tag/Tag.module.css';

interface TagProps {
  color?: string;
  className?: string;
  border?: string;
  text?: string;
  children?: any;
  onClick?: (ev) => void;
  forwardedRef?: React.MutableRefObject<HTMLSpanElement>;
  size?: 'small' | 'medium';
}

const cx = cn.bind(styles);

export const Tag: FC<TagProps> = (props) => {
  const styles = useStyles2(getStyles);
  const { children, color, text, className, border, onClick, size = 'medium' } = props;
  const style: React.CSSProperties = {
    backgroundColor: color,
    color: text,
    border,
  };

  return (
    <span
      style={style}
      className={cx(styles.root, bem(styles.root, size), className, 'test-class-here')}
      onClick={onClick}
      ref={props.forwardedRef}
    >
      {children}
    </span>
  );
};

const getStyles = (_theme: GrafanaTheme2) => {
  return {
    root: css`
      border-radius: 2px;
      line-height: 100%;
      padding: 5px 8px;
      display: inline-block;
      white-space: nowrap;
    `,

    size: css`
      &--small {
        font-size: 12px;
        height: 24px;
      }
    `,
  };
};
