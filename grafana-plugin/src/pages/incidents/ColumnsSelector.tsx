import React, { useState } from 'react';
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';

import { CSS } from '@dnd-kit/utilities';

interface Column {
  id: number | string;
  name: string;
  isChecked?: boolean;
  isHidden?: boolean;
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

const SortableItem: React.FC<Column> = (props) => {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: props.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <span>{props.name}</span>
    </div>
  );
};

export const ExampleSortedList: React.FC = () => {
  const [items, setItems] = useState<Column[]>([...startingColumnsData]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={items} strategy={verticalListSortingStrategy}>
        {items.map(({ id, name }) => (
          <SortableItem key={id} id={id} name={name} />
        ))}
      </SortableContext>
    </DndContext>
  );

  function handleDragEnd(event) {
    const { active, over }: { active: Column; over: Column } = event;

    if (active.id !== over.id) {
      setItems((items) => {
        console.log('Log []');
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);

        return arrayMove(items, oldIndex, newIndex);
      });
    }
  }
};
