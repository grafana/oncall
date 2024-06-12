import React, { useCallback, useRef, useEffect } from 'react';

import { cx } from '@emotion/css';
import { LoadingPlaceholder, useStyles2 } from '@grafana/ui';

import { getGListStyles } from './GList.styles';

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

export const GList = <T extends WithId>(props: GListProps<T>) => {
  const { selectedId, items, onSelect, children, autoScroll } = props;
  const styles = useStyles2(getGListStyles);

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
    <div className={styles.root}>
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
            className={cx(styles.item, { [styles.item_selected]: item.id === selectedId })}
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
