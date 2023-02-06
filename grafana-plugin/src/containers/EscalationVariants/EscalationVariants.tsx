import React, { useState, useCallback, useEffect, useRef } from 'react';

import { SelectableValue } from '@grafana/data';
import {
  RadioButtonGroup,
  ToolbarButton,
  ButtonGroup,
  HorizontalGroup,
  Icon,
  Select,
  IconButton,
  Label,
} from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';

import Avatar from 'components/Avatar/Avatar';
import GTable from 'components/GTable/GTable';
import SearchInput from 'components/SearchInput/SearchInput';
import Text from 'components/Text/Text';
import UserWarning from 'containers/UserWarningModal/UserWarning';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { Schedule } from 'models/schedule/schedule.types';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';
import { useOnClickOutside } from 'utils/hooks';

import { deduplicate } from './EscalationVariants.helpers';
import styles from './EscalationVariants.module.scss';
import { ResponderType, UserAvailability } from './EscalationVariants.types';

const cx = cn.bind(styles);

interface EscalationVariantsProps {
  onUpdateEscalationVariants: (data: any) => void;
  value: { scheduleResponders; userResponders };
  variant?: 'default' | 'primary';
  hideSelected?: boolean;
}

const EscalationVariants = observer(
  ({
    onUpdateEscalationVariants: propsOnUpdateEscalationVariants,
    value,
    variant = 'primary',
    hideSelected = false,
  }: EscalationVariantsProps) => {
    const [showEscalationVariants, setShowEscalationVariants] = useState(false);

    const [showUserWarningModal, setShowUserWarningModal] = useState(false);
    const [selectedUser, setSelectedUser] = useState<User | undefined>(undefined);
    const [userAvailability, setUserAvailability] = useState<UserAvailability | undefined>(undefined);

    const onUpdateEscalationVariants = useCallback((newValue) => {
      const deduplicatedValue = deduplicate(newValue);

      propsOnUpdateEscalationVariants(deduplicatedValue);
    }, []);

    const getUserResponderImportChangeHandler = (index) => {
      return ({ value: important }: SelectableValue<number>) => {
        const userResponders = [...value.userResponders];
        const userResponder = userResponders[index];
        userResponder.important = Boolean(important);

        onUpdateEscalationVariants({
          ...value,
          userResponders,
        });
      };
    };

    const getUserResponderDeleteHandler = (index) => {
      return () => {
        const userResponders = [...value.userResponders];
        userResponders.splice(index, 1);

        onUpdateEscalationVariants({
          ...value,
          userResponders,
        });
      };
    };

    const getScheduleResponderImportChangeHandler = (index) => {
      return ({ value: important }: SelectableValue<number>) => {
        const scheduleResponders = [...value.scheduleResponders];
        const scheduleResponder = scheduleResponders[index];
        scheduleResponder.important = Boolean(important);

        onUpdateEscalationVariants({
          ...value,
          scheduleResponders,
        });
      };
    };

    const getScheduleResponderDeleteHandler = (index) => {
      return () => {
        const scheduleResponders = [...value.scheduleResponders];
        scheduleResponders.splice(index, 1);

        onUpdateEscalationVariants({
          ...value,
          scheduleResponders,
        });
      };
    };

    return (
      <>
        <div className={cx('body')}>
          {!hideSelected && Boolean(value.userResponders.length || value.scheduleResponders.length) && (
            <>
              <Label>Responders:</Label>
              <ul className={cx('responders-list')}>
                {value.userResponders.map((responder, index) => (
                  <UserResponder
                    key={responder.data.pk}
                    onImportantChange={getUserResponderImportChangeHandler(index)}
                    handleDelete={getUserResponderDeleteHandler(index)}
                    {...responder}
                  />
                ))}
                {value.scheduleResponders.map((responder, index) => (
                  <ScheduleResponder
                    onImportantChange={getScheduleResponderImportChangeHandler(index)}
                    handleDelete={getScheduleResponderDeleteHandler(index)}
                    key={responder.data.id}
                    {...responder}
                  />
                ))}
              </ul>
            </>
          )}
          <div className={cx('assign-responders-button')}>
            <ButtonGroup>
              <WithPermissionControl userAction={UserActions.AlertGroupsWrite}>
                <ToolbarButton
                  icon="users-alt"
                  variant={variant}
                  onClick={() => {
                    setShowEscalationVariants(true);
                  }}
                >
                  Add responders
                </ToolbarButton>
              </WithPermissionControl>
              <WithPermissionControl userAction={UserActions.AlertGroupsWrite}>
                <ToolbarButton
                  isOpen={false}
                  narrow
                  variant={variant}
                  onClick={() => {
                    setShowEscalationVariants(true);
                  }}
                />
              </WithPermissionControl>
            </ButtonGroup>
          </div>
          {showEscalationVariants && (
            <EscalationVariantsPopup
              value={value}
              onUpdateEscalationVariants={onUpdateEscalationVariants}
              setShowEscalationVariants={setShowEscalationVariants}
              setSelectedUser={setSelectedUser}
              setShowUserWarningModal={setShowUserWarningModal}
              setUserAvailability={setUserAvailability}
            />
          )}
        </div>
        {showUserWarningModal && (
          <UserWarning
            user={selectedUser}
            userAvailability={userAvailability}
            onHide={() => {
              setShowUserWarningModal(false);
              setSelectedUser(null);
            }}
            onUserSelect={(user: User) => {
              onUpdateEscalationVariants({
                ...value,
                userResponders: [...value.userResponders, { type: ResponderType.User, data: user, important: false }],
              });
            }}
          />
        )}
      </>
    );
  }
);

interface EscalationVariantsPopupProps extends EscalationVariantsProps {
  setShowEscalationVariants: (value: boolean) => void;
  setShowUserWarningModal: (value: boolean) => void;
  setSelectedUser: (user: User) => void;
  setUserAvailability: (data: UserAvailability) => void;
}

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
  const [searchFilters, setSearchFilters] = useState('');

  useEffect(() => {
    store.scheduleStore.updateItems(searchFilters);
    store.userStore.updateItems(searchFilters);
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
        const disabled = value.userResponders.some((userResponder) => userResponder.data.pk === user.pk);
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
        value.userResponders.some((userResponder) => userResponder.data.pk === item.pk) ? <Icon name="check" /> : null,
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
        value={activeOption}
        onChange={handleOptionChange}
        fullWidth
      />
      {activeOption === 'schedules' && (
        <>
          <SearchInput
            key="schedules search"
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
            key="users search"
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
  );
});

const UserResponder = ({ important, data, onImportantChange, handleDelete }) => {
  return (
    <li>
      <HorizontalGroup justify="space-between">
        <HorizontalGroup>
          <div className={cx('timeline-icon-background', { 'timeline-icon-background--green': true })}>
            <Avatar size="big" src={data.avatar} />
          </div>
          <Text>
            {data.username} ({getTzOffsetString(dayjs().tz(data.timezone))})
          </Text>
          <Select
            isSearchable={false}
            value={Number(important)}
            options={[
              { value: 1, label: 'Important' },
              { value: 0, label: 'Default' },
            ]}
            onChange={onImportantChange}
          />
        </HorizontalGroup>
        <IconButton className={cx('trash-button')} name="trash-alt" onClick={handleDelete} />
      </HorizontalGroup>
    </li>
  );
};

const ScheduleResponder = ({ important, data, onImportantChange, handleDelete }) => {
  return (
    <li>
      <HorizontalGroup justify="space-between">
        <HorizontalGroup>
          <div className={cx('timeline-icon-background')}>
            <Icon size="lg" name="calendar-alt" />
          </div>
          <Text>{data.name}</Text>
          <Select
            isSearchable={false}
            value={Number(important)}
            options={[
              { value: 1, label: 'Important' },
              { value: 0, label: 'Default' },
            ]}
            onChange={onImportantChange}
          />
        </HorizontalGroup>
        <IconButton className={cx('trash-button')} name="trash-alt" onClick={handleDelete} />
      </HorizontalGroup>
    </li>
  );
};

export default EscalationVariants;
