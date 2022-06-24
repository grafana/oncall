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

const DragHandle = () => <IconButton name="draggable" />;

const SortableHandleHoc = SortableHandle(DragHandle);

const SortableItem = SortableElement(({ children }) => children);

const SortableList = SortableContainer(({ items, onAddUserGroup }) => {
  return (
    <ul className={cx('groups')}>
      {items.map((item) =>
        item.type === 'item' ? (
          <SortableItem key={item.key} index={item.index}>
            <li className={cx('user')}>
              <div className={cx('user-title')}>
                <Text type="primary"> {item.data.name}</Text> <Text type="secondary">({item.data.tz})</Text>
              </div>
              <div className={cx('user-buttons')}>
                <HorizontalGroup>
                  <IconButton className={cx('delete-icon')} name="trash-alt" />
                </HorizontalGroup>
              </div>
            </li>
          </SortableItem>
        ) : (
          <SortableItem key={item.key} index={item.index}>
            <li className={cx('separator')}>{item.data.name}</li>
          </SortableItem>
        )
      )}
      <SortableItem disabled key="New Group" index={items.length + 1}>
        <li onClick={onAddUserGroup} className={cx('separator', { separator__clickable: true })}>
          Add user group +
        </li>
      </SortableItem>
    </ul>
  );
});

const UserGroups = () => {
  const [groups, setGroups] = useState([[]]);

  const handleAddUserGroup = useCallback(() => {
    setGroups((oldGroups) => [...oldGroups, []]);
  }, [groups]);

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
    ({ value }) => {
      const userAlreadyExist = groups.some((group) => group.some((user) => user.pk === value));

      console.log('userAlreadyExist', userAlreadyExist);

      return !userAlreadyExist;
    },
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
          onAddUserGroup={handleAddUserGroup}
          //useDragHandle
        />
        <GSelect
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
