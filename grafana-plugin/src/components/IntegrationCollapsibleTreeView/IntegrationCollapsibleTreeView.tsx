import React, { useEffect, useState } from 'react';

import { Icon, IconButton, IconName } from '@grafana/ui';
import cn from 'classnames/bind';
import { isArray, isUndefined } from 'lodash-es';
import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';

import styles from './IntegrationCollapsibleTreeView.module.scss';

const cx = cn.bind(styles);

export interface IntegrationCollapsibleItem {
  isHidden?: boolean;
  customIcon?: IconName;
  canHoverIcon?: boolean;
  isTextIcon?: boolean;
  collapsedView?: (toggle?: () => void) => React.ReactNode; // needs toggle param for toggling on click
  expandedView: () => React.ReactNode; // for consistency, this is also a function
  isCollapsible?: boolean;
  isExpanded?: boolean;
  startingElemPosition?: string;
  onStateChange?(isChecked: boolean): void;
}

interface IntegrationCollapsibleTreeViewProps {
  startingElemPosition?: string;
  isRouteView?: boolean;
  configElements: Array<IntegrationCollapsibleItem | IntegrationCollapsibleItem[]>;
}

export const IntegrationCollapsibleTreeView: React.FC<IntegrationCollapsibleTreeViewProps> = observer((props) => {
  const { configElements, isRouteView } = props;

  const [expandedList, setExpandedList] = useState(getStartingExpandedState());

  useEffect(() => {
    setExpandedList(getStartingExpandedState());
  }, [configElements]);

  return (
    <div className={cx('integrationTree__container', isRouteView ? 'integrationTree__container--timeline-view' : '')}>
      {configElements
        .filter((config) => config) // filter out falsy values
        .map((item: IntegrationCollapsibleItem | IntegrationCollapsibleItem[], idx) => {
          if (isArray(item)) {
            return item.map((it, innerIdx) => (
              <IntegrationCollapsibleTreeItem
                item={it}
                key={`${idx}-${innerIdx}`}
                onClick={() => expandOrCollapseAtPos(!expandedList[idx][innerIdx], idx, innerIdx)}
                isExpanded={expandedList[idx][innerIdx]}
              />
            ));
          }

          return (
            <IntegrationCollapsibleTreeItem
              item={item}
              key={idx}
              elementPosition={idx + 1} // start from 1 instead of 0
              onClick={() => expandOrCollapseAtPos(expandedList[idx] as boolean, idx)}
              isExpanded={expandedList[idx] as boolean}
            />
          );
        })}
    </div>
  );

  function getStartingExpandedState(): Array<boolean | boolean[]> {
    const expandedArrayValues = new Array<boolean | boolean[]>(configElements.length);
    configElements.forEach((elem, index) => {
      if (Array.isArray(elem)) {
        expandedArrayValues[index] = elem.map((el) => !el.isCollapsible || el.isExpanded);
      } else {
        expandedArrayValues[index] = !elem.isCollapsible || elem.isExpanded;
      }
    });

    return expandedArrayValues;
  }

  function expandOrCollapseAtPos(isChecked: boolean, i: number, j: number = undefined) {
    if (j !== undefined) {
      let elem = configElements[i] as IntegrationCollapsibleItem[];
      if (elem[j].onStateChange) {
        elem[j].onStateChange(isChecked);
      }
    } else {
      let elem = configElements[i] as IntegrationCollapsibleItem;
      if (elem.onStateChange) {
        elem.onStateChange(isChecked);
      }
    }

    setExpandedList(
      expandedList.map((elem, index) => {
        if (!isUndefined(j) && index === i && Array.isArray(elem)) {
          return (elem as boolean[]).map((innerElem: boolean, jIndex: number) =>
            jIndex === j ? !innerElem : innerElem
          );
        }

        return index === i ? !elem : elem;
      })
    );
  }
});

const IntegrationCollapsibleTreeItem: React.FC<{
  item: IntegrationCollapsibleItem;
  elementPosition?: number;
  isExpanded: boolean;
  onClick: () => void;
}> = ({ item, elementPosition, isExpanded, onClick }) => {
  const handleIconClick = !item.isCollapsible ? undefined : onClick;

  return (
    <div className={cx('integrationTree__group', { 'integrationTree__group--hidden': item.isHidden })}>
      <div
        className={cx('integrationTree__icon')}
        style={{
          transform: `translateY(${item.startingElemPosition || 0})`,
        }}
      >
        {renderIcon()}
      </div>
      <div className={cx('integrationTree__element', { 'integrationTree__element--visible': isExpanded })}>
        {item.expandedView?.()}
      </div>
      <div className={cx('integrationTree__element', { 'integrationTree__element--visible': !isExpanded })}>
        {item.collapsedView?.(onClick)}
      </div>
    </div>
  );

  function renderIcon() {
    if (item.isTextIcon && elementPosition) {
      return (
        <Text type="primary" customTag="h6" className={cx('number-icon')}>
          {elementPosition}
        </Text>
      );
    }

    if (item.canHoverIcon) {
      return <IconButton aria-label="" name={getIconName()} onClick={handleIconClick} size="lg" />;
    }

    return <Icon name={getIconName()} onClick={handleIconClick} size="lg" />;
  }

  function getIconName(): IconName {
    if (item.customIcon) {
      return item.customIcon;
    }
    return isExpanded ? 'angle-down' : 'angle-right';
  }
};
