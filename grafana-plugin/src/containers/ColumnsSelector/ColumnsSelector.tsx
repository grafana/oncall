import React, { useEffect, useMemo, useRef } from 'react';

import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Button, Checkbox, Icon, IconButton, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import { cloneDeep, isEqual, noop } from 'lodash-es';
import { observer } from 'mobx-react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import Text from 'components/Text/Text';
import styles from 'containers/ColumnsSelector/ColumnsSelector.module.scss';
import { AGColumn, AGColumnType } from 'models/alertgroup/alertgroup.types';
import { useStore } from 'state/useStore';
import { openErrorNotification } from 'utils';

const cx = cn.bind(styles);
const TRANSITION_MS = 500;

interface ColumnRowProps {
  column: AGColumn;
  onItemChange: (id: number | string) => void;
}

const ColumnRow: React.FC<ColumnRowProps> = ({ column, onItemChange }) => {
  const dnd = useSortable({ id: column.id });

  const { attributes, listeners, setNodeRef, transform, transition } = dnd;
  const columnElRef = useRef<HTMLDivElement>(undefined);

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={{ ...style }} className={cx('column-row')}>
      <div className={cx('column-item')} ref={columnElRef}>
        <span className={cx('column-name')}>{column.name}</span>

        {column.type === AGColumnType.LABEL && (
          <Tooltip content="Label Column">
            <Icon aria-label="Label" name="tag-alt" className={cx('label-icon')} />
          </Tooltip>
        )}

        {column.isVisible ? (
          <IconButton
            aria-label="Drag"
            name="draggabledots"
            className={cx('column-icon', 'column-icon--drag')}
            {...attributes}
            {...listeners}
          />
        ) : (
          <IconButton
            className={cx('column-icon', 'column-icon--trash')}
            name="trash-alt"
            aria-label="Remove"
            onClick={noop}
          />
        )}
      </div>

      <Checkbox
        className={cx('columns-checkbox')}
        type="checkbox"
        value={column.isVisible}
        onChange={() => onItemChange(column.id)}
      />
    </div>
  );
};

interface ColumnsSelectorProps {
  onModalOpen(): void;
}

export const ColumnsSelector: React.FC<ColumnsSelectorProps> = observer(({ onModalOpen }) => {
  const { alertGroupStore } = useStore();
  const { columns: items, temporaryColumns } = alertGroupStore;

  const visibleColumns = items.filter((col) => col.isVisible);
  const hiddenColumns = items.filter((col) => !col.isVisible);

  useEffect(() => {
    if (!temporaryColumns.length) {
      alertGroupStore.temporaryColumns = cloneDeep(items);
    }
  }, []);

  const canResetData = useMemo(
    () => !isEqual(temporaryColumns, items),
    [alertGroupStore.columns, alertGroupStore.temporaryColumns]
  );

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  return (
    <div className={cx('columns-selector-view')}>
      <Text type="primary" className={cx('columns-header')}>
        Fields Settings
      </Text>

      <div className={cx('columns-visible-section')}>
        <Text type="primary" className={cx('columns-header-small')}>
          Visible ({visibleColumns.length})
        </Text>

        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={(ev) => handleDragEnd(ev, true)}>
          <SortableContext items={items} strategy={verticalListSortingStrategy}>
            <TransitionGroup>
              {visibleColumns.map((column) => (
                <CSSTransition key={column.id} timeout={TRANSITION_MS} unmountOnExit classNames="fade">
                  <ColumnRow key={column.id} column={column} onItemChange={onItemChange} />
                </CSSTransition>
              ))}
            </TransitionGroup>
          </SortableContext>
        </DndContext>
      </div>

      <div className={cx('columns-hidden-section')}>
        <Text type="primary" className={cx('columns-header-small')}>
          Hidden ({hiddenColumns.length})
        </Text>

        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={(ev) => handleDragEnd(ev, false)}>
          <SortableContext items={items} strategy={verticalListSortingStrategy}>
            <TransitionGroup>
              {hiddenColumns.map((column) => (
                <CSSTransition key={column.id} timeout={TRANSITION_MS} classNames="fade">
                  <ColumnRow key={column.id} column={column} onItemChange={onItemChange} />
                </CSSTransition>
              ))}
            </TransitionGroup>
          </SortableContext>
        </DndContext>
      </div>

      <div className={cx('columns-selector-buttons')}>
        <Button variant={'secondary'} disabled={!canResetData} onClick={onReset}>
          Reset
        </Button>
        <Button variant={'primary'} icon="plus" onClick={onModalOpen}>
          Add column
        </Button>
      </div>
    </div>
  );

  function onReset() {
    alertGroupStore.columns = [...alertGroupStore.temporaryColumns];
  }

  function onItemChange(id: string | number) {
    const checkedItems = alertGroupStore.columns.filter((col) => col.isVisible);
    if (checkedItems.length === 1 && checkedItems[0].id === id) {
      openErrorNotification('At least one column should be selected');
      return;
    }

    alertGroupStore.columns = alertGroupStore.columns.map((item): AGColumn => {
      let newItem: AGColumn = { ...item, isVisible: !item.isVisible };
      return item.id === id ? newItem : item;
    });
  }

  function handleDragEnd(event: DragEndEvent, isVisible: boolean) {
    const { active, over } = event;

    let searchableList: AGColumn[] = isVisible ? visibleColumns : hiddenColumns;

    if (active.id !== over.id) {
      const oldIndex = searchableList.findIndex((item) => item.id === active.id);
      const newIndex = searchableList.findIndex((item) => item.id === over.id);

      searchableList = arrayMove(searchableList, oldIndex, newIndex);

      const updatedList = isVisible ? [...searchableList, ...hiddenColumns] : [...visibleColumns, ...searchableList];
      alertGroupStore.columns = updatedList;
    }
  }
});
