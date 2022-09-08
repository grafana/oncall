import React, { FC, useCallback, useEffect, useMemo, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { VerticalGroup, HorizontalGroup, IconButton, Field, Input } from '@grafana/ui';
import { arrayMoveImmutable } from 'array-move';
import cn from 'classnames/bind';
import { SortableContainer, SortableElement, SortableHandle } from 'react-sortable-hoc';

import Text from 'components/Text/Text';
import WorkingHours from 'components/WorkingHours/WorkingHours';
import GSelect from 'containers/GSelect/GSelect';
import UserTooltip from 'containers/UserTooltip/UserTooltip';
import { User } from 'models/user/user.types';

import { fromPlainArray, toPlainArray } from './UserGroups.helpers';
import { Item, ItemData } from './UserGroups.types';

import styles from './UserGroups.module.css';

interface UserGroupsProps {
  value: Array<Array<User['pk']>>;
  onChange: (value: Array<Array<User['pk']>>) => void;
  isMultipleGroups: boolean;
  getItemData: (id: string) => ItemData;
  renderUser: (id: string) => React.ReactElement;
  showError?: boolean;
}

const cx = cn.bind(styles);

const DragHandle = () => <IconButton name="draggabledots" />;

const SortableHandleHoc = SortableHandle(DragHandle);

const UserGroups = (props: UserGroupsProps) => {
  const { value, onChange, isMultipleGroups, getItemData, renderUser, showError } = props;

  const handleAddUserGroup = useCallback(() => {
    onChange([...value, []]);
  }, [value]);

  const handleDeleteUser = (index: number) => {
    const newGroups = [...value];
    let k = -1;
    for (let i = 0; i < value.length; i++) {
      k++;
      const users = value[i];
      for (let j = 0; j < users.length; j++) {
        k++;

        if (k === index) {
          newGroups[i] = newGroups[i].filter((item, itemIndex) => itemIndex !== j);
          onChange(newGroups.filter((group) => group.length));
          return;
        }
      }
    }
  };

  const handleUserAdd = useCallback(
    (pk: User['pk'], user: User) => {
      if (!pk) {
        return;
      }

      const newGroups = [...value];
      let lastGroup = newGroups[newGroups.length - 1];
      if (!lastGroup) {
        lastGroup = [];
        newGroups.push(lastGroup);
      }

      lastGroup.push(pk);

      onChange(newGroups);
    },
    [value]
  );

  const items = useMemo(() => toPlainArray(value, getItemData), [value]);

  const onSortEnd = useCallback(
    ({ oldIndex, newIndex }) => {
      const newPlainArray = arrayMoveImmutable(items, oldIndex, newIndex);

      onChange(fromPlainArray(newPlainArray, newIndex > items.length));
    },
    [items]
  );

  const getDeleteItemHandler = (index: number) => {
    return () => {
      handleDeleteUser(index);
    };
  };

  const renderItem = (item: Item, index: number) => (
    <li className={cx('user')}>
      {renderUser(item.item)}
      <div className={cx('user-buttons')}>
        <HorizontalGroup>
          <IconButton className={cx('delete-icon')} name="trash-alt" onClick={getDeleteItemHandler(index)} />
          <SortableHandleHoc />
        </HorizontalGroup>
      </div>
    </li>
  );

  return (
    <div className={cx('root')}>
      <VerticalGroup>
        <SortableList
          renderItem={renderItem}
          axis="y"
          lockAxis="y"
          helperClass={cx('sortable-helper')}
          items={items}
          onSortEnd={onSortEnd}
          handleAddGroup={handleAddUserGroup}
          handleDeleteItem={handleDeleteUser}
          isMultipleGroups={isMultipleGroups}
          useDragHandle
        />
        <GSelect
          key={items.length} // to completely rerender when users length change
          showSearch
          allowClear
          modelName="userStore"
          displayField="username"
          valueField="pk"
          placeholder="Add user"
          className={cx('select')}
          value={null}
          onChange={handleUserAdd}
          getOptionLabel={({ label, value }: SelectableValue) => <UserTooltip id={value} />}
          showError={showError}
        />
      </VerticalGroup>
    </div>
  );
};

interface SortableItemProps {
  children: React.ReactElement;
}

const SortableItem = SortableElement(({ children }: SortableItemProps) => children);

interface SortableListProps {
  items: Item[];
  handleAddGroup: () => void;
  handleDeleteItem: (index: number) => void;
  isMultipleGroups: boolean;
  renderItem: (item: Item, index: number) => React.ReactElement;
}

const SortableList = SortableContainer(
  ({ items, handleAddGroup, handleDeleteItem, isMultipleGroups, renderItem }: SortableListProps) => {
    return (
      <ul className={cx('groups')}>
        {items.map((item, index) =>
          item.type === 'item' ? (
            <SortableItem key={item.key} index={index}>
              {renderItem(item, index)}
            </SortableItem>
          ) : isMultipleGroups ? (
            <SortableItem key={item.key} index={index}>
              <li className={cx('separator')}>{item.data.name}</li>
            </SortableItem>
          ) : null
        )}
        {isMultipleGroups && items[items.length - 1]?.type === 'item' && (
          <SortableItem disabled key="New Group" index={items.length + 1}>
            <li onClick={handleAddGroup} className={cx('separator', { separator__clickable: true })}>
              Add user group +
            </li>
          </SortableItem>
        )}
      </ul>
    );
  }
);

export default UserGroups;
