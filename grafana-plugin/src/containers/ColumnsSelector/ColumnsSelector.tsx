import React, { useMemo, useRef } from 'react';

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
import { Button, Checkbox, Icon, IconButton, LoadingPlaceholder, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import { isEqual } from 'lodash-es';
import { observer } from 'mobx-react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import Text from 'components/Text/Text';
import styles from 'containers/ColumnsSelector/ColumnsSelector.module.scss';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AGColumn, AGColumnType } from 'models/alertgroup/alertgroup.types';
import { ActionKey } from 'models/loader/action-keys';
import { LoaderStore } from 'models/loader/loader';
import { useStore } from 'state/useStore';
import { openErrorNotification } from 'utils';
import { UserActions } from 'utils/authorization';
import { WrapAutoLoadingState } from 'utils/decorators';

const cx = cn.bind(styles);
const TRANSITION_MS = 500;

interface ColumnRowProps {
  column: AGColumn;
  onItemChange: (id: number | string) => void;
  onColumnRemoval: (column: AGColumn) => void;
}

const ColumnRow: React.FC<ColumnRowProps> = ({ column, onItemChange, onColumnRemoval }) => {
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
        ) : column.type === AGColumnType.LABEL ? (
          <WithPermissionControlTooltip userAction={UserActions.OtherSettingsWrite}>
            <IconButton
              className={cx('column-icon', 'column-icon--trash')}
              name="trash-alt"
              aria-label="Remove"
              tooltip={'Remove column'}
              onClick={() => onColumnRemoval(column)}
            />
          </WithPermissionControlTooltip>
        ) : undefined}
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
  onColumnAddModalOpen(): void;
  onConfirmRemovalModalOpen(column: AGColumn): void;
}

export const ColumnsSelector: React.FC<ColumnsSelectorProps> = observer(
  ({ onColumnAddModalOpen, onConfirmRemovalModalOpen }) => {
    const { alertGroupStore } = useStore();
    const { columns } = alertGroupStore;

    const visibleColumns = columns.filter((col) => col.isVisible);
    const hiddenColumns = columns
      .filter((col) => !col.isVisible)
      .sort((a, b) => a.id.toString().localeCompare(b.id.toString()));

    const canResetData = useMemo(() => !isEqual(columns, getDefaultData()), [alertGroupStore.columns]);

    const sensors = useSensors(
      useSensor(PointerSensor),
      useSensor(KeyboardSensor, {
        coordinateGetter: sortableKeyboardCoordinates,
      })
    );

    const isResetLoading = LoaderStore.isLoading(ActionKey.IS_RESETING_COLUMNS_FROM_ALERT_GROUP);

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
            <SortableContext items={columns} strategy={verticalListSortingStrategy}>
              <TransitionGroup>
                {visibleColumns.map((column) => (
                  <CSSTransition key={column.id} timeout={TRANSITION_MS} unmountOnExit classNames="fade">
                    <ColumnRow
                      key={column.id}
                      column={column}
                      onItemChange={onItemChange}
                      onColumnRemoval={onConfirmRemovalModalOpen}
                    />
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
            <SortableContext items={columns} strategy={verticalListSortingStrategy}>
              <TransitionGroup>
                {hiddenColumns.map((column) => (
                  <CSSTransition key={column.id} timeout={TRANSITION_MS} classNames="fade">
                    <ColumnRow
                      key={column.id}
                      column={column}
                      onItemChange={onItemChange}
                      onColumnRemoval={onConfirmRemovalModalOpen}
                    />
                  </CSSTransition>
                ))}
              </TransitionGroup>
            </SortableContext>
          </DndContext>
        </div>

        <div className={cx('columns-selector-buttons')}>
          <Button
            variant={'secondary'}
            disabled={!canResetData || isResetLoading}
            onClick={WrapAutoLoadingState(onReset, ActionKey.IS_RESETING_COLUMNS_FROM_ALERT_GROUP)}
          >
            {isResetLoading ? <LoadingPlaceholder text="Loading..." className="loadingPlaceholder" /> : 'Reset'}
          </Button>
          <WithPermissionControlTooltip userAction={UserActions.OtherSettingsWrite}>
            <Button variant={'primary'} disabled={isResetLoading} icon="plus" onClick={onColumnAddModalOpen}>
              Add column
            </Button>
          </WithPermissionControlTooltip>
        </div>
      </div>
    );

    async function onReset() {
      const columnsDefaultValues = getDefaultData();

      return alertGroupStore
        .updateTableSettings(columnsDefaultValues, true)
        .then(() => alertGroupStore.fetchTableSettings());
    }

    function getDefaultData() {
      const { columns } = alertGroupStore;

      const columnsDefaultValues: { visible: AGColumn[]; hidden: AGColumn[] } = {
        visible: columns
          .filter((col) => col.type === AGColumnType.DEFAULT)
          .sort((a, b) => (a.id as number) - (b.id as number)),
        hidden: columns
          .filter((col) => col.type === AGColumnType.LABEL)
          .sort((a, b) => a.id.toString().localeCompare(b.id.toString())),
      };

      return columnsDefaultValues;
    }

    async function onItemChange(id: string | number) {
      const checkedItems = alertGroupStore.columns.filter((col) => col.isVisible);
      if (checkedItems.length === 1 && checkedItems[0].id === id) {
        openErrorNotification('At least one column should be selected');
        return;
      }

      alertGroupStore.columns = alertGroupStore.columns.map((item): AGColumn => {
        let newItem: AGColumn = { ...item, isVisible: !item.isVisible };
        return item.id === id ? newItem : item;
      });

      await alertGroupStore.updateTableSettings(convertColumnsToTableSettings(alertGroupStore.columns), true);
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
  }
);

export function convertColumnsToTableSettings(columns: AGColumn[]): { visible: AGColumn[]; hidden: AGColumn[] } {
  const tableSettings: { visible: AGColumn[]; hidden: AGColumn[] } = {
    visible: columns.filter((col: AGColumn) => col.isVisible),
    hidden: columns.filter((col: AGColumn) => !col.isVisible),
  };

  return tableSettings;
}
