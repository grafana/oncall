import React, { useState, useCallback, useEffect, useRef } from 'react';

import { Icon, Input, RadioButtonGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import GTable from 'components/GTable/GTable';
import Text from 'components/Text/Text';
import { EscalationVariantsProps } from 'containers/EscalationVariants/EscalationVariants';
import styles from 'containers/EscalationVariants/EscalationVariants.module.scss';
import { ResponderType, UserAvailability } from 'containers/EscalationVariants/EscalationVariants.types';
import { Schedule } from 'models/schedule/schedule.types';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';
import { useDebouncedCallback, useOnClickOutside } from 'utils/hooks';

interface EscalationVariantsPopupProps extends EscalationVariantsProps {
  setShowEscalationVariants: (value: boolean) => void;
  setShowUserWarningModal: (value: boolean) => void;
  setSelectedUser: (user: User) => void;
  setUserAvailability: (data: UserAvailability) => void;
}

const cx = cn.bind(styles);

const EscalationVariantsPopup = observer((props: EscalationVariantsPopupProps) => {
  const {
    onUpdateEscalationVariants,
    setShowEscalationVariants,
    value,
    setSelectedUser,
    setShowUserWarningModal,
    setUserAvailability,
  } = props;

  const store = useStore();

  const [activeOption, setActiveOption] = useState('schedules');
  const [usersSearchTerm, setUsersSearchTerm] = useState('');
  const [schedulesSearchTerm, setSchedulesSearchTerm] = useState('');

  const handleSetSchedulesSearchTerm = useCallback((e) => {
    setSchedulesSearchTerm(e.target.value);
  }, []);

  const handleSetUsersSearchTerm = useCallback((e) => {
    setUsersSearchTerm(e.target.value);
  }, []);

  const handleOptionChange = useCallback((option: string) => {
    setActiveOption(option);
  }, []);

  const addUserResponders = (user: User) => {
    store.userStore.checkUserAvailability(user.pk).then((res) => {
      setSelectedUser(user);
      setUserAvailability(res);
      setShowUserWarningModal(true);
    });

    setShowEscalationVariants(false);
  };

  const addSchedulesResponders = (schedule: Schedule) => {
    setShowEscalationVariants(false);
    onUpdateEscalationVariants({
      ...value,
      scheduleResponders: [
        ...value.scheduleResponders,
        { type: ResponderType.Schedule, data: schedule, important: false },
      ],
    });
  };

  const handleUsersSearchTermChange = useDebouncedCallback(() => {
    store.userStore.updateItems(usersSearchTerm);
  }, 500);

  useEffect(handleUsersSearchTermChange, [usersSearchTerm]);

  const handleSchedulesSearchTermChange = useDebouncedCallback(() => {
    store.scheduleStore.updateItems(schedulesSearchTerm);
  }, 500);

  useEffect(handleSchedulesSearchTermChange, [schedulesSearchTerm]);

  const scheduleColumns = [
    {
      width: 300,
      render: (schedule: Schedule) => {
        const disabled = value.scheduleResponders.some(
          (scheduleResponder) => scheduleResponder.data.id === schedule.id
        );

        return (
          <div
            onClick={() => (disabled ? undefined : addSchedulesResponders(schedule))}
            className={cx('responder-item')}
          >
            <Text type={disabled ? 'disabled' : undefined}>{schedule.name}</Text>
          </div>
        );
      },
      key: 'Title',
    },
    {
      width: 40,
      render: (item: Schedule) =>
        value.scheduleResponders.some((scheduleResponder) => scheduleResponder.data.id === item.id) ? (
          <Icon name="check" />
        ) : null,
      key: 'Checked',
    },
  ];

  const userColumns = [
    {
      width: 300,
      render: (user: User) => {
        const disabled = value.userResponders.some((userResponder) => userResponder.data?.pk === user.pk);
        return (
          <div onClick={() => (disabled ? undefined : addUserResponders(user))} className={cx('responder-item')}>
            <Text type={disabled ? 'disabled' : undefined}>
              {user.username} ({user.timezone})
            </Text>
          </div>
        );
      },
      key: 'username',
    },
    {
      width: 40,
      render: (item: User) =>
        value.userResponders.some((userResponder) => userResponder.data?.pk === item.pk) ? <Icon name="check" /> : null,
      key: 'Checked',
    },
  ];

  const ref = useRef();

  useOnClickOutside(ref, () => {
    setShowEscalationVariants(false);
  });

  return (
    <div ref={ref} className={cx('escalation-variants-dropdown')}>
      <RadioButtonGroup
        options={[
          { value: 'schedules', label: 'Schedules' },
          { value: 'users', label: 'Users' },
        ]}
        className={cx('radio-buttons')}
        value={activeOption}
        onChange={handleOptionChange}
        fullWidth
      />
      {activeOption === 'schedules' && (
        <>
          <Input
            prefix={<Icon name="search" />}
            key="schedules search"
            className={cx('responders-filters')}
            value={schedulesSearchTerm}
            placeholder="Search schedules..."
            // @ts-ignore
            width={'unset'}
            onChange={handleSetSchedulesSearchTerm}
          />
          <GTable
            emptyText={store.scheduleStore.getSearchResult()?.results ? 'No schedules found' : 'Loading...'}
            rowKey="id"
            columns={scheduleColumns}
            data={store.scheduleStore.getSearchResult()?.results}
            className={cx('table')}
            showHeader={false}
          />
        </>
      )}
      {activeOption === 'users' && (
        <>
          <Input
            prefix={<Icon name="search" />}
            key="users search"
            // @ts-ignore
            width={'unset'}
            className={cx('responders-filters')}
            placeholder="Search users..."
            value={usersSearchTerm}
            onChange={handleSetUsersSearchTerm}
          />
          <GTable
            emptyText={store.userStore.getSearchResult()?.results ? 'No users found' : 'Loading...'}
            rowKey="id"
            columns={userColumns}
            data={store.userStore.getSearchResult()?.results}
            className={cx('table')}
            showHeader={false}
          />
        </>
      )}
    </div>
  );
});

export default EscalationVariantsPopup;
