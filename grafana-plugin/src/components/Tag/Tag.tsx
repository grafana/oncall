import React, { FC } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { useStyles2 } from '@grafana/ui';
import { bem } from 'styles/utils.styles';

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
      className={cx(styles.root, bem(styles.root, size), className)}
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
      color: #fff;
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
