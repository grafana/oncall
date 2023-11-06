import React, { useState } from 'react';

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

import Text from 'components/Text/Text';
import styles from 'pages/incidents/ColumnsSelector.module.scss';

const cx = cn.bind(styles);

interface Column {
  id: number | string;
  name: string;
  isChecked?: boolean;
  isHidden?: boolean;
}

interface ColumnRowProps {
  column: Column;
  onItemChange: (id: number | string) => void;
}

const startingColumnsData: Column[] = [
  { id: 1, name: 'Status', isChecked: true },
  { id: 2, name: 'ID', isChecked: true },
  { id: 3, name: 'Summary', isChecked: true },
  { id: 4, name: 'Integration', isChecked: true },
  { id: 5, name: 'Users', isChecked: true },
  { id: 6, name: 'Team', isChecked: true },
  { id: 7, name: 'Cortex', isHidden: true },
  { id: 8, name: 'Created', isHidden: true },
];

const ColumnRow: React.FC<ColumnRowProps> = ({ column, onItemChange }) => {
  const dnd = useSortable({ id: column.id });

  const { attributes, listeners, setNodeRef, transform, transition } = dnd;

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={{ ...style }} className={cx('column-row')}>
      <div className={cx('column-item')}>
        <span className={cx('column-name')}>{column.name}</span>

        {column.isChecked ? (
          <IconButton
            aria-label="Drag"
            name="draggabledots"
            className={cx('column-icon', 'column-icon--drag')}
            {...attributes}
            {...listeners}
          />
        ) : (
          <IconButton className={cx('column-icon', 'column-icon--trash')} name="trash-alt" aria-label="Remove" />
        )}
      </div>

      <Checkbox
        className={cx('columns-checkbox')}
        type="checkbox"
        value={column.isChecked}
        onChange={() => onItemChange(column.id)}
      />
    </div>
  );
};

interface ColumnsSelectorProps {
  onModalOpen(): void;
}

export const ColumnsSelector: React.FC<ColumnsSelectorProps> = ({ onModalOpen }) => {
  const [items, setItems] = useState<Column[]>([...startingColumnsData]);
  const visibleColumns = items.filter((col) => col.isChecked);
  const hiddenColumns = items.filter((col) => !col.isChecked);

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
            {visibleColumns.map((column) => (
              <ColumnRow key={column.id} column={column} onItemChange={onItemChange} />
            ))}
          </SortableContext>
        </DndContext>
      </div>

      <div className={cx('columns-hidden-section')}>
        <Text type="primary" className={cx('columns-header-small')}>
          Hidden ({hiddenColumns.length})
        </Text>

        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={(ev) => handleDragEnd(ev, false)}>
          <SortableContext items={items} strategy={verticalListSortingStrategy}>
            {hiddenColumns.map((column) => (
              <ColumnRow key={column.id} column={column} onItemChange={onItemChange} />
            ))}
          </SortableContext>
        </DndContext>
      </div>

      <div className={cx('columns-selector-buttons')}>
        <Button variant={'secondary'}>Reset</Button>
        <Button variant={'primary'} icon="plus" onClick={onModalOpen}>
          Add field
        </Button>
      </div>
    </div>
  );

  function onItemChange(id: string | number) {
    setItems((items) => {
      return items.map((it) => (it.id === id ? { ...it, isChecked: !it.isChecked } : it));
    });
  }

  function handleDragEnd(event: DragEndEvent, isVisible: boolean) {
    const { active, over } = event;

    let searchableList: Column[] = isVisible ? visibleColumns : hiddenColumns;

    if (active.id !== over.id) {
      const oldIndex = searchableList.findIndex((item) => item.id === active.id);
      const newIndex = searchableList.findIndex((item) => item.id === over.id);

      searchableList = arrayMove(searchableList, oldIndex, newIndex);

      const updatedList = isVisible ? [...searchableList, ...hiddenColumns] : [...visibleColumns, ...searchableList];
      setItems(updatedList);
    }
  }
};
