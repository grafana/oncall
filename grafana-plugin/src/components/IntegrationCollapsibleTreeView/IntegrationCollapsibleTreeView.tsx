import React from 'react';
import cn from 'classnames/bind';

import styles from './IntegrationCollapsibleTreeView.module.scss';

const cx = cn.bind(styles);

interface IntegrationCollapsibleTreeViewProps {
  children: React.ReactNode[]
}

const IntegrationCollapsibleTreeView: React.FC<IntegrationCollapsibleTreeViewProps> = () => {
  return <div className={cx('integrationTree__container')}></div>;
};

export default IntegrationCollapsibleTreeView;
