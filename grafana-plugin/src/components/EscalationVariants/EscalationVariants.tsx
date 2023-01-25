import React, { useState, useCallback, useEffect } from 'react';

import { RadioButtonGroup, Button } from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';

import GTable from 'components/GTable/GTable';
import SearchInput from 'components/SearchInput/SearchInput';
import UserWarning from 'components/UserWarningModal/UserWarning';
import { Schedule } from 'models/schedule/schedule.types';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import styles from './EscalationVariants.module.css';

const cx = cn.bind(styles);

interface EscalationVariantsProps {
  onUpdateEscalationVariants: (data: any) => void;
  value: { schedulesIds; usersIds };
}

// interface AssignRespondersPickerProps {
//   value: any;
//   handleAddResponders: (id) => void;
//   respondersOption: string;
// }

// const AssignRespondersPicker = (props: AssignRespondersPickerProps) => {
//   const { value = { searchTerm: '' }, handleAddResponders, respondersOption } = props;
//   const store = useStore();
//   console.log('respondersOption', respondersOption);

//   const onSearchTermChangeCallback = useCallback(
//     (e: ChangeEvent<HTMLInputElement>) => {
//       const filters = {
//         ...value,
//         searchTerm: e.currentTarget.value,
//       };

//       if (respondersOption == 'schedules') {
//         store.scheduleStore.updateItems(filters);
//       }
//       if (respondersOption == 'users') {
//         store.userStore.updateItems(filters);
//       }
//     },
//     [value]
//   );
//     //   const respondersList = currentStore.getSearchResult();
//     if (respondersOption == 'schedules') {
//       const scheculesList = store.scheduleStore.getSearchResult();
//     }
//     if (respondersOption == 'users') {
//       const usersList = store.userStore.getSearchResult();
//     }

//   return (
//     <div className={cx('assign-responders-picker')}>
//       <Input
//         prefix={<Icon name="search" />}
//         className={cx('search', 'control')}
//         placeholder="Search"
//         value={value.searchTerm}
//         onChange={onSearchTermChangeCallback}
//       />
//       <div className={cx('assign-responders-list')}>
//         {respondersOption == 'schedules'
//           ? store.scheduleStore.getSearchResult()?.map((schedule) => (
//               <div
//                 key={schedule.id}
//                 className={cx('assign-responders-item')}
//                 onClick={() => handleAddResponders(schedule)}
//               >
//                 {schedule.name}
//               </div>
//             ))
//           : store.userStore.getSearchResult()?.map((user) => (
//               <div key={user.pk} className={cx('assign-responders-item')} onClick={() => handleAddResponders(user)}>
//                 {user.name}
//               </div>
//             ))}
//       </div>
//     </div>
//   );
// };

const EscalationVariants = observer(({ onUpdateEscalationVariants, value }: EscalationVariantsProps) => {
  const store = useStore();
  const [activeOption, setActiveOption] = useState('schedules');
  const [showEscalationVariants, setShowEscalationVariants] = useState(false);
  const [searchFilters, setSearchFilters] = useState('');
  const [responders, setResponders] = useState([]);
  const [showUserWarningModal, setShowUserWarningModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);

  useEffect(() => {
    store.scheduleStore.updateItems(searchFilters);
    store.userStore.updateItems(searchFilters);
  }, []);

  const handleOpenEscalationVariants = (status) => {
    if (status) {
      setShowEscalationVariants(false);
    } else {
      setShowEscalationVariants(true);
    }
  };

  const handleOptionChange = useCallback((option: string) => {
    setActiveOption(option);
  }, []);

  const addUserResponders = (user: User) => {
    store.userStore.checkUserAvailability(user.pk).then((res) => {
      console.log('AVAILABILITY', res.warnings);
      if (res.warnings.length > 0) {
        console.log('IF', res.warnings.length);
        setShowUserWarningModal(true);
        setSelectedUser(user);
      }
    });

    setResponders((responders) => [...responders, user]);
    setShowEscalationVariants(false);
    onUpdateEscalationVariants({ ...value, usersIds: [...value.usersIds, { id: user.pk, important: false }] });
  };

  const addSchedulesResponders = (schedule: Schedule) => {
    setResponders((responders) => [...responders, schedule]);
    setShowEscalationVariants(false);
    onUpdateEscalationVariants({
      ...value,
      schedulesIds: [...value.schedulesIds, { id: schedule.id, important: false }],
    });
  };

  const renderScheduleName = (schedule: Schedule) => {
    return (
      <div onClick={() => addSchedulesResponders(schedule)} className={cx('responder-item')}>
        {schedule.name}
      </div>
    );
  };

  const renderUserName = (user: User) => {
    return (
      <div onClick={() => addUserResponders(user)} className={cx('responder-item')}>
        {user.username} ({user.timezone})
      </div>
    );
  };

  const debouncedUpdateUsers = debounce(() => store.userStore.updateItems(searchFilters), 500);
  const debouncedUpdateSchedule = debounce(() => store.scheduleStore.updateItems(searchFilters), 500);

  const handleSearchFilterChange = (searchFilters: any) => {
    setSearchFilters(searchFilters);
    if (activeOption === 'users') {
      debouncedUpdateUsers();
    } else {
      debouncedUpdateSchedule();
    }
  };

  const scheduleColumns = [
    {
      width: 300,
      render: renderScheduleName,
      key: 'Title',
    },
  ];

  const userColumns = [
    {
      width: 300,
      render: renderUserName,
      key: 'username',
    },
  ];
  return (
    <>
      <div>
        {responders.map((responder) => (
          <div key={responder.id || responder.pk}>{responder.name || responder.username}</div>
        ))}
        <div className={cx('assign-responders-button')}>
          <Button variant="secondary">Add responders</Button>
          <Button
            variant="secondary"
            onClick={() => handleOpenEscalationVariants(showEscalationVariants)}
            icon="angle-down"
            style={{ width: '24px' }}
          ></Button>
        </div>
        {showEscalationVariants && (
          <div className={cx('escalation-variants-dropdown')}>
            <RadioButtonGroup
              options={[
                { value: 'schedules', label: 'Schedules' },
                { value: 'users', label: 'Users' },
              ]}
              value={activeOption}
              onChange={handleOptionChange}
              fullWidth
            />
            {activeOption === 'schedules' && (
              <>
                <SearchInput
                  className={cx('responders-filters')}
                  value={searchFilters}
                  onChange={handleSearchFilterChange}
                />
                <GTable
                  emptyText={store.scheduleStore.getSearchResult() ? 'No schedules found' : 'Loading...'}
                  rowKey="id"
                  columns={scheduleColumns}
                  data={store.scheduleStore.getSearchResult()}
                  className={cx('schedule-table')}
                  showHeader={false}
                />
              </>
            )}
            {activeOption === 'users' && (
              <>
                <SearchInput
                  className={cx('responders-filters')}
                  value={searchFilters}
                  onChange={handleSearchFilterChange}
                />
                <GTable
                  emptyText={store.userStore.getSearchResult().results ? 'No users found' : 'Loading...'}
                  rowKey="id"
                  columns={userColumns}
                  data={store.userStore.getSearchResult().results}
                  className={cx('schedule-table')}
                  showHeader={false}
                />
              </>
            )}
          </div>
        )}
        {showUserWarningModal && (
          <UserWarning
            user={selectedUser}
            onHide={() => {
              setShowUserWarningModal(false);
              setSelectedUser(null);
            }}
          />
        )}
      </div>
    </>
  );
});

export default EscalationVariants;
