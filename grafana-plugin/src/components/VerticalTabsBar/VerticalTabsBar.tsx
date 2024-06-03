import React, { FC } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { useStyles2 } from '@grafana/ui';
import { bem } from 'styles/utils.styles';
interface TabProps {
  id: string;
  children?: any;
}

export const VerticalTab: FC<TabProps> = ({ children }) => {
  return <>{children}</>;
};

interface VerticalTabsBarProps {
  children: Array<React.ReactElement<TabProps>> | React.ReactElement<TabProps>;
  activeTab: string;
  onChange: (id: string) => void;
}

export const VerticalTabsBar = (props: VerticalTabsBarProps) => {
  const { children, activeTab, onChange } = props;
  const styles = useStyles2(getStyles);

  const getClickHandler = (id: string) => {
    return () => {
      onChange(id);
    };
  };

  return (
    <div className={styles.root}>
      {React.Children.toArray(children)
        .filter(Boolean)
        .map((child: React.ReactElement, idx) => (
          <div
            key={idx}
            onClick={getClickHandler(child.props.id)}
            className={cx(styles.tab, { [bem(styles.tab, 'active')]: activeTab === child.props.id })}
          >
            {child}
          </div>
        ))}
    </div>
  );
};

const getStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      display: flex;
      flex-direction: column;
    `,

    tab: css`
      cursor: pointer;
      position: relative;
      padding: 12px;
      opacity: 0.8;

      &:hover {
        background: ${theme.colors.background.secondary};
        opacity: 1;
      }

      &--active {
        cursor: default;
        opacity: 1;

        &::before {
          display: block;
          content: '';
          position: absolute;
          left: 0;
          top: 12px;
          bottom: 12px;
          width: 4px;
          background-image: linear-gradient(270deg, #f55f3e 0%, #f83 100%);
        }
      }
    `,
  };
};
