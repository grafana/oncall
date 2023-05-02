import React, { useState } from 'react';

import { IconButton } from '@grafana/ui';
import cn from 'classnames/bind';
import { isArray, isUndefined } from 'lodash-es';

import styles from './IntegrationCollapsibleTreeView.module.scss';

const cx = cn.bind(styles);

export interface IntegrationCollapsibleItem {
  expandedView: React.ReactNode;
  collapsedView: React.ReactNode;
  isCollapsible: boolean;
}

interface IntegrationCollapsibleTreeViewProps {
  configElements: Array<IntegrationCollapsibleItem | IntegrationCollapsibleItem[]>;
}

const IntegrationCollapsibleTreeView: React.FC<IntegrationCollapsibleTreeViewProps> = (props) => {
  const { configElements } = props;

  const [expandedList, setExpandedList] = useState(getStartingExpandedState());

  return (
    <div className={cx('integrationTree__container')}>
      {configElements.map((item: IntegrationCollapsibleItem | IntegrationCollapsibleItem[], idx) => {
        if (isArray(item)) {
          return item.map((it, innerIdx) => (
            <IntegrationCollapsibleTreeItem
              item={it}
              key={`${idx}-${innerIdx}`}
              onClick={() => expandOrCollapseAtPos(idx, innerIdx)}
              isExpanded={!!expandedList[idx][innerIdx]}
            />
          ));
        }

        return (
          <IntegrationCollapsibleTreeItem
            item={item}
            key={idx}
            onClick={() => expandOrCollapseAtPos(idx)}
            isExpanded={!!expandedList[idx]}
          />
        );
      })}
    </div>
  );

  function getStartingExpandedState(): (boolean | boolean[])[] {
    const expandedArrayValues = new Array<boolean | boolean[]>(configElements.length);
    configElements.forEach((elem, index) => {
      expandedArrayValues[index] = Array.isArray(elem) ? new Array(elem.length).fill(true) : true;
    });

    return expandedArrayValues;
  }

  function expandOrCollapseAtPos(i: number, j: number = undefined) {
    setExpandedList(
      expandedList.map((elem, index) => {
        if (!isUndefined(j) && index === i) {
          return (elem as boolean[]).map((innerElem: boolean, jIndex: number) =>
            jIndex === j ? !innerElem : innerElem
          );
        }

        return index === i ? !elem : elem;
      })
    );
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
        <IconButton
          name={!item.isCollapsible ? 'plus' : isExpanded ? 'arrow-down' : 'arrow-right'}
          onClick={!item.isCollapsible ? undefined : onClick}
          size="lg"
        />
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
