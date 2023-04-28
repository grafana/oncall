import React, { useState } from 'react';

import { Icon } from '@grafana/ui';
import cn from 'classnames/bind';

import styles from './IntegrationCollapsibleTreeView.module.scss';
import { isArray } from 'lodash-es';

const cx = cn.bind(styles);

export interface IntegrationCollapsibleItem {
  expandedView: React.ReactNode;
  collapsedView: React.ReactNode;
  isCollapsible: boolean;
}

interface IntegrationCollapsibleTreeViewProps {
  configElements: (IntegrationCollapsibleItem | IntegrationCollapsibleItem[])[];
}

const IntegrationCollapsibleTreeView: React.FC<IntegrationCollapsibleTreeViewProps> = (props) => {
  const { configElements } = props;
  const [expandedList, setExpandedList] = useState(new Array<boolean>(configElements.length).fill(true));

  return (
    <div className={cx('integrationTree__container')}>
      {configElements.map((item: IntegrationCollapsibleItem | IntegrationCollapsibleItem[], idx) => {
        if (isArray(item)) {
          return item.map((it) => (
            <IntegrationCollapsibleTreeItem
              item={it}
              onClick={() => expandOrCollapseAtPos(idx)}
              isExpanded={!!expandedList[idx]}
            />
          ));
        }

        return (
          <IntegrationCollapsibleTreeItem
            item={item}
            onClick={() => expandOrCollapseAtPos(idx)}
            isExpanded={!!expandedList[idx]}
          />
        );
      })}
    </div>
  );

  function expandOrCollapseAtPos(i) {
    setExpandedList(expandedList.map((elem, index) => (index === i ? !elem : elem)));
    setTimeout(() => console.log(expandedList));
  }
};

const IntegrationCollapsibleTreeItem: React.FC<{ item: IntegrationCollapsibleItem; isExpanded: boolean; onClick }> = ({
  item,
  isExpanded,
  onClick,
}) => {
  return (
    <div className={cx('integrationTree__group')}>
      <div className={cx('integrationTree__icon')}>
        <Icon name={isExpanded ? 'arrow-down' : 'arrow-right'} size="lg" onClick={onClick} />
      </div>
      <div className={cx('integrationTree__element', { 'integrationTree__element--visible': isExpanded })}>
        {item.expandedView}
      </div>
      <div className={cx('integrationTree__element', { 'integrationTree__element--visible': !isExpanded })}>
        {item.collapsedView}
      </div>
    </div>
  );
};

export default IntegrationCollapsibleTreeView;
