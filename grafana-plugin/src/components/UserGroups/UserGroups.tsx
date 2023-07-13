import React, { useCallback, useEffect, useMemo, useRef } from 'react';

import { VerticalGroup, HorizontalGroup, IconButton } from '@grafana/ui';
import { arrayMoveImmutable } from 'array-move';
import cn from 'classnames/bind';
import { SortableContainer, SortableElement, SortableHandle } from 'react-sortable-hoc';

import Text from 'components/Text/Text';
import RemoteSelect from 'containers/RemoteSelect/RemoteSelect';
import { User } from 'models/user/user.types';
import { UserActions } from 'utils/authorization';

import { fromPlainArray, toPlainArray } from './UserGroups.helpers';
import { Item } from './UserGroups.types';

import styles from './UserGroups.module.css';

interface UserGroupsProps {
  value: Array<Array<User['pk']>>;
  onChange: (value: Array<Array<User['pk']>>) => void;
  isMultipleGroups: boolean;
  renderUser: (id: string) => React.ReactElement;
  showError?: boolean;
  disabled?: boolean;
}

const cx = cn.bind(styles);

const DragHandle = () => <IconButton className={cx('icon')} name="draggabledots" />;

const SortableHandleHoc = SortableHandle(DragHandle);

const UserGroups = (props: UserGroupsProps) => {
  const { value, onChange, isMultipleGroups, renderUser, showError, disabled } = props;

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
          newGroups[i] = newGroups[i].filter((_item, itemIndex) => itemIndex !== j);
          onChange(newGroups.filter((group) => group.length));
          return;
        }
      }
    }
  };

  const handleUserAdd = useCallback(
    (pk: User['pk']) => {
      if (!pk) {
        return;
      }

      const newGroups = [...value];
      let lastGroup = newGroups[newGroups.length - 1];
      if (!isMultipleGroups || (lastGroup && !lastGroup.length)) {
        if (!lastGroup) {
          lastGroup = [];
          newGroups.push(lastGroup);
        }
        lastGroup.push(pk);
      } else {
        newGroups.push([pk]);
      }

      onChange(newGroups);
    },
    [value]
  );

  const items = useMemo(() => toPlainArray(value), [value]);

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
      {renderUser(item.data)}
      {!disabled && (
        <div className={cx('user-buttons')}>
          <HorizontalGroup>
            <IconButton className={cx('icon')} name="trash-alt" onClick={getDeleteItemHandler(index)} />
            <SortableHandleHoc />
          </HorizontalGroup>
        </div>
      )}
    </li>
  );

  return (
    <div className={cx('root')}>
      <VerticalGroup>
        {!disabled && (
          <RemoteSelect
            key={items.length}
            showSearch
            placeholder="Add user"
            href={`/users/?permission=${UserActions.NotificationsRead.permission}&filters=true`}
            value={null}
            onChange={handleUserAdd}
            showError={showError}
            maxMenuHeight={150}
            requiredUserAction={UserActions.UserSettingsWrite}
          />
        )}
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
          allowCreate={!disabled}
        />
      </VerticalGroup>
    </div>
  );
};

interface SortableItemProps {
  children: React.ReactElement;
}

const SortableItem = SortableElement<SortableItemProps>(({ children }) => children);

interface SortableListProps {
  items: Item[];
  handleAddGroup: () => void;
  handleDeleteItem: (index: number) => void;
  isMultipleGroups: boolean;
  renderItem: (item: Item, index: number) => React.ReactElement;
  allowCreate?: boolean;
}

const SortableList = SortableContainer<SortableListProps>(
  ({ items, handleAddGroup, isMultipleGroups, renderItem, allowCreate }) => {
    const listRef = useRef<HTMLUListElement>();

    useEffect(() => {
      const container = listRef.current;

      container.scroll({
        left: 0,
        top: container.scrollHeight,
        behavior: 'smooth',
      });
    }, [items]);

    return (
      <ul className={cx('groups')} ref={listRef}>
        {items.map((item, index) =>
          item.type === 'item' ? (
            <SortableItem key={item.key} index={index}>
              {renderItem(item, index)}
            </SortableItem>
          ) : isMultipleGroups ? (
            <SortableItem key={item.key} index={index}>
              <li className={cx('separator')}>
                <Text type="secondary">{item.data.name}</Text>
              </li>
            </SortableItem>
          ) : null
        )}
        {allowCreate && isMultipleGroups && items[items.length - 1]?.type === 'item' && (
          <SortableItem disabled key="New Group" index={items.length + 1}>
            <li onClick={handleAddGroup} className={cx('separator', { separator__clickable: true })}>
              <Text type="primary">+ Add user group</Text>
            </li>
          </SortableItem>
        )}
      </ul>
    );
  }
);

export default UserGroups;
