import React, { FC, useCallback, useEffect, useMemo, useState } from 'react';

import { VerticalGroup, HorizontalGroup, IconButton } from '@grafana/ui';
import { arrayMoveImmutable } from 'array-move';
import cn from 'classnames/bind';
import { SortableContainer, SortableElement, SortableHandle } from 'react-sortable-hoc';

import Text from 'components/Text/Text';

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
  const [groups, setGroups] = useState(getRandomGroups());

  const handleAddUserGroup = useCallback(() => {
    setGroups((oldGroups) => [...oldGroups, []]);
  }, [groups]);

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
        {/* <div className={cx('add-user-group')} onClick={handleAddUserGroup}>
          Add user group +
        </div>*/}
      </VerticalGroup>
    </div>
  );
};

export default UserGroups;
