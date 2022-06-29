import React, { FC, useCallback, useEffect, useMemo, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { VerticalGroup, HorizontalGroup, IconButton, Field, Input } from '@grafana/ui';
import { arrayMoveImmutable } from 'array-move';
import cn from 'classnames/bind';
import { SortableContainer, SortableElement, SortableHandle } from 'react-sortable-hoc';

import Text from 'components/Text/Text';
import GSelect from 'containers/GSelect/GSelect';
import UserTooltip from 'containers/UserTooltip/UserTooltip';
import { User } from 'models/user/user.types';
import { getRandomTimezone } from 'pages/schedule/Schedule.helpers';

import { fromPlainArray, getRandomGroups, toPlainArray } from './UserGroups.helpers';

import styles from './UserGroups.module.css';

interface UserGroupsProps {}

const cx = cn.bind(styles);

const DragHandle = () => <IconButton name="draggabledots" />;

const SortableHandleHoc = SortableHandle(DragHandle);

const SortableItem = SortableElement(({ children }) => children);

const SortableList = SortableContainer(({ items, handleAddGroup, handleDeleteItem }) => {
  const getDeleteItemHandler = (index) => {
    return () => {
      handleDeleteItem(index);
    };
  };

  return (
    <ul className={cx('groups')}>
      {items.map((item, index) =>
        item.type === 'item' ? (
          <SortableItem key={item.key} index={index}>
            <li className={cx('user')}>
              <div className={cx('user-title')}>
                <Text type="primary"> {item.data.name}</Text> <Text type="secondary">({item.data.tz})</Text>
              </div>
              <div className={cx('user-buttons')}>
                <HorizontalGroup>
                  <IconButton className={cx('delete-icon')} name="trash-alt" onClick={getDeleteItemHandler(index)} />
                  <SortableHandleHoc />
                </HorizontalGroup>
              </div>
            </li>
          </SortableItem>
        ) : (
          <SortableItem key={item.key} index={index}>
            <li className={cx('separator')}>{item.data.name}</li>
          </SortableItem>
        )
      )}
      {items[items.length - 1]?.type === 'item' && (
        <SortableItem disabled key="New Group" index={items.length + 1}>
          <li onClick={handleAddGroup} className={cx('separator', { separator__clickable: true })}>
            Add user group +
          </li>
        </SortableItem>
      )}
    </ul>
  );
});

const UserGroups = () => {
  const [groups, setGroups] = useState([[]]);

  const handleAddUserGroup = useCallback(() => {
    setGroups((oldGroups) => [...oldGroups, []]);
  }, [groups]);

  const handleDeleteUser = (index: number) => {
    const newGroups = [...groups];
    let k = -1;
    for (let i = 0; i < groups.length; i++) {
      k++;
      const users = groups[i];
      for (let j = 0; j < users.length; j++) {
        k++;

        if (k === index) {
          newGroups[i] = newGroups[i].filter((item, itemIndex) => itemIndex !== j);
          setGroups(newGroups.filter((group, index) => index === 0 || group.length));
          return;
        }
      }
    }
  };

  const handleUserAdd = useCallback((pk: User['pk'], user: User) => {
    if (!pk) {
      return;
    }

    setGroups((groups) => {
      const newGroups = [...groups];
      const lastGroup = newGroups[groups.length - 1];

      lastGroup.push({ pk, name: user.username, tz: getRandomTimezone() });

      return newGroups;
    });
  }, []);

  const filterUsers = useCallback(
    ({ value }) => !groups.some((group) => group.some((user) => user.pk === value)),
    [groups]
  );

  const items = useMemo(() => toPlainArray(groups), [groups]);

  const onSortEnd = useCallback(
    ({ oldIndex, newIndex, collection, isKeySorting }) => {
      const newPlainArray = arrayMoveImmutable(items, oldIndex, newIndex);

      setGroups(fromPlainArray(newPlainArray, newIndex > items.length));
    },
    [items]
  );

  return (
    <div className={cx('root')}>
      <VerticalGroup>
        <SortableList
          axis="y"
          lockAxis="y"
          helperClass={cx('sortable-helper')}
          items={items}
          onSortEnd={onSortEnd}
          handleAddGroup={handleAddUserGroup}
          handleDeleteItem={handleDeleteUser}
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
          filterOptions={filterUsers}
        />
      </VerticalGroup>
    </div>
  );
};

export default UserGroups;
