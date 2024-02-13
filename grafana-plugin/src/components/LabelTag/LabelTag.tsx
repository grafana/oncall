import React from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { HorizontalGroup, getTagColorsFromName, useStyles2 } from '@grafana/ui';
import tinycolor2 from 'tinycolor2';

export interface LabelTagProps {
  label: string;
  value: string;
  size?: LabelTagSize;
}

export type LabelTagSize = 'md' | 'sm';

export const LabelTag: React.FC<LabelTagProps> = (props: LabelTagProps) => {
  const { label, value, size = 'sm' } = props;

  const color = getLabelColor(label);

  const styles = useStyles2((theme) => getStyles(theme, color, size));

  return (
    <div className={styles.wrapper} role="listitem">
      <HorizontalGroup spacing="none">
        <div className={styles.label}>{label ?? ''}</div>
        <div className={styles.value}>{value}</div>
      </HorizontalGroup>
    </div>
  );
};

function getLabelColor(input: string): string {
  return getTagColorsFromName(input).color;
}

const getStyles = (theme: GrafanaTheme2, color?: string, size?: string) => {
  const backgroundColor = color ?? theme.colors.secondary.main;

  const borderColor = theme.isDark
    ? tinycolor2(backgroundColor).lighten(5).toString()
    : tinycolor2(backgroundColor).darken(5).toString();

  const valueBackgroundColor = theme.isDark
    ? tinycolor2(backgroundColor).darken(5).toString()
    : tinycolor2(backgroundColor).lighten(5).toString();

  const fontColor = color
    ? tinycolor2.mostReadable(backgroundColor, ['#000', '#fff']).toString()
    : theme.colors.text.primary;

  const padding =
    size === 'md' ? `${theme.spacing(0.33)} ${theme.spacing(1)}` : `${theme.spacing(0.2)} ${theme.spacing(0.6)}`;

  return {
    wrapper: css`
      color: ${fontColor};
      font-size: ${theme.typography.bodySmall.fontSize};

      border-radius: ${theme.shape.borderRadius(2)};
    `,
    label: css`
      display: flex;
      align-items: center;
      color: inherit;

      padding: ${padding};
      background: ${backgroundColor};

      border: solid 1px ${borderColor};
      border-top-left-radius: ${theme.shape.borderRadius(2)};
      border-bottom-left-radius: ${theme.shape.borderRadius(2)};
    `,
    value: css`
      color: inherit;
      padding: ${padding};
      background: ${valueBackgroundColor};

      border: solid 1px ${borderColor};
      border-left: none;
      border-top-right-radius: ${theme.shape.borderRadius(2)};
      border-bottom-right-radius: ${theme.shape.borderRadius(2)};
    `,
  };
};
