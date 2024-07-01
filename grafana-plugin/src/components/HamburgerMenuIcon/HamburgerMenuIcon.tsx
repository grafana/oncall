import React, { useRef } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Icon, useStyles2 } from '@grafana/ui';
import { bem } from 'styles/utils.styles';

interface HamburgerMenuIconProps {
  openMenu: React.MouseEventHandler<HTMLElement>;
  listWidth: number;
  listBorder: number;
  stopPropagation?: boolean;
  withBackground?: boolean;
  className?: string;
}

export const HamburgerMenuIcon: React.FC<HamburgerMenuIconProps> = (props) => {
  const ref = useRef<HTMLDivElement>();
  const styles = useStyles2(getHamburgerMenuIconStyles);
  const { openMenu, listBorder, listWidth, withBackground, className, stopPropagation = false } = props;
  return (
    <div
      ref={ref}
      className={cx(styles.hamburgerMenu, { [bem(styles.hamburgerMenu, 'withBackground')]: withBackground }, className)}
      onClick={(e) => {
        if (stopPropagation) {
          e.stopPropagation();
        }

        const boundingRect = ref.current.getBoundingClientRect();

        openMenu({
          pageX: boundingRect.right - listWidth + listBorder * 2,
          pageY: boundingRect.top + boundingRect.height,
        } as any);
      }}
    >
      <Icon size="sm" name="ellipsis-v" />
    </div>
  );
};

const getHamburgerMenuIconStyles = (theme: GrafanaTheme2) => {
  return {
    hamburgerMenu: css`
      cursor: pointer;
      color: ${theme.colors.text.primary};
      display: inline-flex;
      flex-direction: column;
      align-items: center;
      vertical-align: middle;
      justify-content: center;
      padding: 4px;

      &--withBackground {
        height: 32px;
        width: 30px;
        cursor: pointer;
      }

      &--small {
        height: 24px;
        width: 22px;
        cursor: pointer;
      }
    `,
  };
};
