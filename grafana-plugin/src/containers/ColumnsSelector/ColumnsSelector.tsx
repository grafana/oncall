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
import { restrictToVerticalAxis, restrictToFirstScrollableAncestor } from '@dnd-kit/modifiers';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Button, Checkbox, Icon, IconButton, LoadingPlaceholder, Tooltip, useStyles2 } from '@grafana/ui';
import { observer } from 'mobx-react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Text } from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertGroupColumn, AlertGroupColumnType } from 'models/alertgroup/alertgroup.types';
import { ActionKey } from 'models/loader/action-keys';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization/authorization';
import { useIsLoading } from 'utils/hooks';
import { openErrorNotification } from 'utils/utils';

import { getColumnsSelectorStyles } from './ColumnsSelector.styles';

const TRANSITION_MS = 500;
const KEY_DELIMITATOR = '/-/';

interface ColumnRowProps {
  column: AlertGroupColumn;
  onItemChange: (column: AlertGroupColumn) => void;
  onColumnRemoval: (column: AlertGroupColumn) => void;
}

function getColumnCombinedID(column: AlertGroupColumn) {
  return `${column.id}${KEY_DELIMITATOR}${column.type}`;
}

const ColumnRow: React.FC<ColumnRowProps> = ({ column, onItemChange, onColumnRemoval }) => {
  const dnd = useSortable({
    id: getColumnCombinedID(column),
    data: {
      id: column.id,
    },
  });

  const styles = useStyles2(getColumnsSelectorStyles);

  const { attributes, listeners, setNodeRef, transform, transition } = dnd;
  const columnElRef = useRef<HTMLDivElement>(undefined);

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={{ ...style }} className={styles.columnRow}>
      <div className={styles.columnItem} ref={columnElRef}>
        <span className={styles.columnName}>{column.name}</span>

        {column.type === AlertGroupColumnType.LABEL && (
          <Tooltip content="Label Column">
            <Icon aria-label="Label" name="tag-alt" className={styles.labelIcon} />
          </Tooltip>
        )}

        <RenderConditionally shouldRender={column.isVisible}>
          <IconButton
            aria-label="Drag"
            name="draggabledots"
            className={styles.columnsIcon}
            {...attributes}
            {...listeners}
          />
        </RenderConditionally>

        <RenderConditionally shouldRender={!column.isVisible && column.type === AlertGroupColumnType.LABEL}>
          <WithPermissionControlTooltip userAction={UserActions.OtherSettingsWrite}>
            <IconButton
              className={[styles.columnsIcon, styles.columnsIconTrash, 'columns-icon-trash'].join(' ')}
              name="trash-alt"
              aria-label="Remove"
              tooltip={'Remove column'}
              onClick={() => onColumnRemoval(column)}
            />
          </WithPermissionControlTooltip>
        </RenderConditionally>
      </div>

      <Checkbox
        className={styles.columnsCheckbox}
        type="checkbox"
        value={column.isVisible}
        onChange={() => onItemChange(column)}
      />
    </div>
  );
};

interface ColumnsSelectorProps {
  onColumnAddModalOpen(): void;
  onConfirmRemovalModalOpen(column: AlertGroupColumn): void;
}

export const ColumnsSelector: React.FC<ColumnsSelectorProps> = observer(
  ({ onColumnAddModalOpen, onConfirmRemovalModalOpen }) => {
    const { alertGroupStore } = useStore();
    const isResetLoading = useIsLoading(ActionKey.RESET_COLUMNS_FROM_ALERT_GROUP);

    const styles = useStyles2(getColumnsSelectorStyles);

    const { columns, isDefaultColumnOrder } = alertGroupStore;

    const visibleColumns = columns.filter((col) => col.isVisible);
    const hiddenColumns = columns
      .filter((col) => !col.isVisible)
      .sort((a, b) => a.id.toString().localeCompare(b.id.toString()));

    const sensors = useSensors(
      useSensor(PointerSensor),
      useSensor(KeyboardSensor, {
        coordinateGetter: sortableKeyboardCoordinates,
      })
    );

    return (
      <div className={styles.columnsSelectorView}>
        <Text type="primary" className={styles.columnsHeader}>
          Columns Settings
        </Text>

        <div className={styles.columnsVisibleSection}>
          <Text type="primary" className={styles.columnsHeaderSmall}>
            Visible ({visibleColumns.length})
          </Text>

          <DndContext
            autoScroll={{ layoutShiftCompensation: false }}
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={(ev) => handleDragEnd(ev, true)}
            modifiers={[restrictToVerticalAxis, restrictToFirstScrollableAncestor]}
          >
            <SortableContext items={mapColumnsToDndItems(visibleColumns)} strategy={verticalListSortingStrategy}>
              <TransitionGroup>
                {visibleColumns.map((column) => (
                  <CSSTransition
                    key={getColumnCombinedID(column)}
                    timeout={TRANSITION_MS}
                    unmountOnExit
                    classNames="fade"
                  >
                    <ColumnRow
                      key={getColumnCombinedID(column)}
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

        <div className={styles.columnsHiddenSection}>
          <Text type="primary" className={styles.columnsHeaderSmall}>
            Hidden ({hiddenColumns.length})
          </Text>

          <DndContext
            autoScroll={{ layoutShiftCompensation: false }}
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={(ev) => handleDragEnd(ev, false)}
          >
            <SortableContext items={mapColumnsToDndItems(hiddenColumns)} strategy={verticalListSortingStrategy}>
              <TransitionGroup>
                {hiddenColumns.map((column) => (
                  <CSSTransition key={getColumnCombinedID(column)} timeout={TRANSITION_MS} classNames="fade">
                    <ColumnRow
                      key={getColumnCombinedID(column)}
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

        <div className={styles.columnsSelectorButtons}>
          <Button
            variant={'secondary'}
            tooltipPlacement="top"
            tooltip={'Reset table to default columns'}
            disabled={isResetLoading || isDefaultColumnOrder}
            onClick={() => alertGroupStore.resetColumns()}
          >
            {isResetLoading ? <LoadingPlaceholder text="Loading..." className="loadingPlaceholder" /> : 'Reset'}
          </Button>
          <WithPermissionControlTooltip userAction={UserActions.OtherSettingsWrite}>
            <Button variant={'primary'} disabled={isResetLoading} icon="plus" onClick={onColumnAddModalOpen}>
              Add
            </Button>
          </WithPermissionControlTooltip>
        </div>
      </div>
    );

    function mapColumnsToDndItems(columns: AlertGroupColumn[]) {
      return columns.map((col) => ({
        ...col,
        id: getColumnCombinedID(col),
      }));
    }

    async function onItemChange({ id, type }: AlertGroupColumn) {
      const checkedItems = alertGroupStore.columns.filter((col) => col.isVisible);
      if (checkedItems.length === 1 && checkedItems[0].id === id) {
        openErrorNotification('At least one column should be selected');
        return;
      }

      alertGroupStore.columns = alertGroupStore.columns.map((item): AlertGroupColumn => {
        let newItem: AlertGroupColumn = { ...item, isVisible: !item.isVisible };
        return item.id === id && item.type === type ? newItem : item;
      });

      await alertGroupStore.updateTableSettings(convertColumnsToTableSettings(alertGroupStore.columns), true);
    }

    function handleDragEnd(event: DragEndEvent, isVisible: boolean) {
      const { active, over } = event;

      let searchableList: AlertGroupColumn[] = isVisible ? visibleColumns : hiddenColumns;

      if (active.id !== over.id) {
        const oldIndex = searchableList.findIndex((item) => getColumnCombinedID(item) === active.id);
        const newIndex = searchableList.findIndex((item) => getColumnCombinedID(item) === over.id);

        searchableList = arrayMove(searchableList, oldIndex, newIndex);

        const updatedList = isVisible ? [...searchableList, ...hiddenColumns] : [...visibleColumns, ...searchableList];

        alertGroupStore.columns = updatedList;
      }
    }
  }
);

export function convertColumnsToTableSettings(columns: AlertGroupColumn[]): {
  visible: AlertGroupColumn[];
  hidden: AlertGroupColumn[];
} {
  const tableSettings: { visible: AlertGroupColumn[]; hidden: AlertGroupColumn[] } = {
    visible: columns.filter((col: AlertGroupColumn) => col.isVisible),
    hidden: columns.filter((col: AlertGroupColumn) => !col.isVisible),
  };

  return tableSettings;
}
