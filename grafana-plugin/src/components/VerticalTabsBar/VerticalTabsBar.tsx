import React, { FC } from 'react';

import cn from 'classnames/bind';

import styles from './VerticalTabsBar.module.css';

interface VerticalTabsBarProps {
  children: Array<React.ReactElement<TabProps>> | React.ReactElement<TabProps>;
  activeTab: string;
  onChange: (id: string) => void;
}

const cx = cn.bind(styles);

const VerticalTabsBar = (props: VerticalTabsBarProps) => {
  const { children, activeTab, onChange } = props;

  const getClickHandler = (id: string) => {
    return () => {
      onChange(id);
    };
  };

  return (
    <div className={cx('root')}>
      {React.Children.toArray(children)
        .filter(Boolean)
        .map((child: React.ReactElement) => (
          <div
            onClick={getClickHandler(child.props.id)}
            className={cx('tab', { tab_active: activeTab === child.props.id })}
          >
            {child}
          </div>
        ))}
    </div>
  );
};

export default VerticalTabsBar;

interface TabProps {
  id: string;
}

export const VerticalTab: FC<TabProps> = ({ children }) => {
  return <>{children}</>;
};
