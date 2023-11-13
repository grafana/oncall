import React, { useRef } from 'react';

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
import { Button, Checkbox, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';
import { noop } from 'lodash-es';
import { observer } from 'mobx-react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import Text from 'components/Text/Text';
import { AGColumn } from 'models/alertgroup/alertgroup.types';
import styles from 'pages/incidents/ColumnsSelector.module.scss';
import { useStore } from 'state/useStore';

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
  const { columns: items } = alertGroupStore;

  const visibleColumns = items.filter((col) => col.isVisible);
  const hiddenColumns = items.filter((col) => !col.isVisible);

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
        <Button variant={'secondary'} onClick={onReset}>
          Reset
        </Button>
        <Button variant={'primary'} icon="plus" onClick={onModalOpen}>
          Add field
        </Button>
      </div>
    </div>
  );

  function onReset() {}

  function onItemChange(id: string | number) {
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
