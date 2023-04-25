import React from 'react';

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
          return itemNode().map((innerItemNode: React.ReactNode, innerIndex: number) =>
            renderNode(innerItemNode, innerIndex)
          );
        }

        return renderNode(itemNode, index);
      })}
    </div>
  );

  function renderNode(node: React.ReactNode, key) {
    return (
      <div className={cx('integrationTree__group')} key={key}>
        <div className={cx('integrationTree__icon')}>
          <Icon name="arrow-down" size="lg" />
        </div>
        {node}
      </div>
    );
  }
};

export default IntegrationCollapsibleTreeView;
