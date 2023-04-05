import React from 'react';
import cn from 'classnames/bind';

import styles from './IntegrationCollapsibleTreeView.module.scss';
import { Icon } from '@grafana/ui';

const cx = cn.bind(styles);

interface IntegrationCollapsibleTreeViewProps {
  children: React.ReactNode[];
}

const IntegrationCollapsibleTreeView: React.FC<IntegrationCollapsibleTreeViewProps> = (props) => {
  const { children } = props;
  return (
    <div className={cx('integrationTree__container')}>
      {children.map((itemNode: React.ReactNode) => {
        return (
          <div className={cx('integrationTree__group')}>
            <div className={cx('integrationTree__icon')}>
              <Icon name="arrow-down" />
            </div>
            {itemNode}
          </div>
        );
      })}
    </div>
  );
};

export default IntegrationCollapsibleTreeView;
