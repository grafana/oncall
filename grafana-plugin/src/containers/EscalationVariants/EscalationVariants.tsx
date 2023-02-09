import React, { useState, useCallback } from 'react';

import { SelectableValue } from '@grafana/data';
import { ToolbarButton, ButtonGroup, HorizontalGroup, Icon, Select, IconButton, Label } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import Avatar from 'components/Avatar/Avatar';
import Text from 'components/Text/Text';
import UserWarning from 'containers/UserWarningModal/UserWarning';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { getTzOffsetString } from 'models/timezone/timezone.helpers';
import { User } from 'models/user/user.types';
import { UserActions } from 'utils/authorization';

import { deduplicate } from './EscalationVariants.helpers';
import styles from './EscalationVariants.module.scss';
import { ResponderType, UserAvailability } from './EscalationVariants.types';
import EscalationVariantsPopup from './parts/EscalationVariantsPopup';

const cx = cn.bind(styles);

export interface EscalationVariantsProps {
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
                    key={responder.data?.pk}
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

const UserResponder = ({ important, data, onImportantChange, handleDelete }) => {
  return (
    <li>
      <HorizontalGroup justify="space-between">
        <HorizontalGroup>
          <div className={cx('timeline-icon-background', { 'timeline-icon-background--green': true })}>
            <Avatar size="big" src={data?.avatar} />
          </div>
          <Text>
            {data?.username} ({getTzOffsetString(dayjs().tz(data?.timezone))})
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
