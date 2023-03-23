import React, { useCallback, useRef, useEffect } from 'react';

import { LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';

import styles from './GList.module.css';

const cx = cn.bind(styles);

export interface GListProps<T> {
  selectedId: string;
  items: T[];
  children: (item: T) => React.ReactNode;
  itemKey?: string;
  onSelect?: (id: string) => void;
  autoScroll?: boolean;
}

interface WithId {
  id: string;
}

const GList = <T extends WithId>(props: GListProps<T>) => {
  const { selectedId, items, onSelect, children, autoScroll } = props;

  const getitemClickHandler = useCallback((id: string) => {
    return () => {
      onSelect && onSelect(id);
    };
  }, []);

  const itemsRef = useRef(null);

  useEffect(() => {
    if (autoScroll && selectedId) {
      const map = getMap();
      const selectedElement = map.get(selectedId);

      if (!selectedElement) {
        return;
      }

      const divToScroll = selectedElement.parentElement.parentElement;

      const maxScroll = Math.max(0, selectedElement.parentElement.offsetHeight - divToScroll.offsetHeight);

      const scrollTop =
        selectedElement.offsetTop -
        selectedElement.parentElement.offsetTop -
        selectedElement.parentElement.parentElement.offsetHeight / 2;

      divToScroll.scroll({
        left: 0,
        top: Math.max(0, Math.min(maxScroll, scrollTop)),
        behavior: 'smooth',
      });
    }
  }, [selectedId, autoScroll]);

  function getMap() {
    if (!itemsRef.current) {
      itemsRef.current = new Map();
    }
    return itemsRef.current;
  }

  return (
    <div className={cx('root')}>
      {items ? (
        items.map((item) => (
          <div
            ref={(node) => {
              const map = getMap();
              if (node) {
                map.set(item.id, node);
              } else {
                map.delete(item.id);
              }
            }}
            key={item.id}
            className={cx('item', { item_selected: item.id === selectedId })}
            onClick={getitemClickHandler(item.id)}
          >
            {children(item)}
          </div>
        ))
      ) : (
        <LoadingPlaceholder text="Loading..." />
      )}
    </div>
  );
};

export default GList;
