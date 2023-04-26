import React, { useState } from 'react';

import { Icon } from '@grafana/ui';
import cn from 'classnames/bind';

import styles from './IntegrationCollapsibleTreeView.module.scss';
import { isFunction } from 'lodash-es';

const cx = cn.bind(styles);

interface IntegrationCollapsibleTreeViewProps {
  children: (React.ReactNode | (() => React.ReactNode))[];
}

const IntegrationCollapsibleTreeView: React.FC<IntegrationCollapsibleTreeViewProps> = (props) => {
  const { children } = props;

  return (
    <div className={cx('integrationTree__container')}>
      {children.map((itemNode: React.ReactNode | (() => React.ReactNode[]), index: number) => {
        if (isFunction(itemNode)) {
          return itemNode().map((innerItemNode: React.ReactNode, innerIndex: number) => {
            return <IntegrationCollapsibleTreeItem node={innerItemNode} key={`${index}-${innerIndex}`} />;
          });
        }

        return <IntegrationCollapsibleTreeItem node={itemNode} key={`${index}-0`} />;
      })}
    </div>
  );
};

const IntegrationCollapsibleTreeItem: React.FC<{ node: React.ReactNode; key: string }> = ({ node, key }) => {
  const [isCollapsed, setIsCollapsed] = useState(true);
  return (
    <div className={cx('integrationTree__group')} key={key}>
      <div className={cx('integrationTree__icon')}>
        <Icon
          name={isCollapsed ? 'arrow-down' : 'arrow-right'}
          size="lg"
          onClick={() => setIsCollapsed(!isCollapsed)}
        />
      </div>
      {isCollapsed && <>{node}</>}
    </div>
  );
};

export default IntegrationCollapsibleTreeView;
