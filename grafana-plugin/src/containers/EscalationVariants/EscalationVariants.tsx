import React, { useState, useCallback } from 'react';

import { SelectableValue } from '@grafana/data';
import { HorizontalGroup, Icon, Select, IconButton, Label, Tooltip, Button } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Avatar from 'components/Avatar/Avatar';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import UserWarning from 'containers/UserWarningModal/UserWarning';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
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
  variant?: 'secondary' | 'primary';
  hideSelected?: boolean;
  disabled?: boolean;
  withLabels?: boolean;
}

const EscalationVariants = observer(
  ({
    onUpdateEscalationVariants: propsOnUpdateEscalationVariants,
    value,
    variant = 'primary',
    hideSelected = false,
    disabled,
    withLabels = false,
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
              <Label>Additional responders will be notified immediately:</Label>
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
            {withLabels && <Label>Additional responders (optional)</Label>}
            <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
              <Button
                icon="users-alt"
                variant={variant}
                disabled={disabled}
                onClick={() => {
                  setShowEscalationVariants(true);
                }}
              >
                Notify additional responders
              </Button>
            </WithPermissionControlTooltip>
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
                userResponders: [
                  ...value.userResponders,
                  {
                    type: ResponderType.User,
                    data: user,
                    important:
                      user.notification_chain_verbal.important && !user.notification_chain_verbal.default
                        ? true
                        : false,
                  },
                ],
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
          <Text className={cx('responder-name')}>{data?.username}</Text>
          {data.notification_chain_verbal.default || data.notification_chain_verbal.important ? (
            <HorizontalGroup>
              <Text type="secondary">by</Text>
              <Select
                className={cx('select')}
                width="auto"
                isSearchable={false}
                value={Number(important)}
                options={[
                  {
                    value: 0,
                    label: 'Default',
                    description: 'Use "Default notifications" from user\'s personal settings',
                  },
                  {
                    value: 1,
                    label: 'Important',
                    description: 'Use "Important notifications" from user\'s personal settings',
                  },
                ]}
                // @ts-ignore
                isOptionDisabled={({ value }) =>
                  (value === 0 && !data.notification_chain_verbal.default) ||
                  (value === 1 && !data.notification_chain_verbal.important)
                }
                getOptionLabel={({ value, label }) => {
                  return (
                    <Text
                      type={
                        (value === 0 && !data.notification_chain_verbal.default) ||
                        (value === 1 && !data.notification_chain_verbal.important)
                          ? 'disabled'
                          : 'primary'
                      }
                    >
                      {label}
                    </Text>
                  );
                }}
                onChange={onImportantChange}
              />
              <Text type="secondary">notification policies</Text>
            </HorizontalGroup>
          ) : (
            <HorizontalGroup>
              <Tooltip content="User doesn't have configured notification policies">
                <Icon name="exclamation-triangle" style={{ color: 'var(--error-text-color)' }} />
              </Tooltip>
            </HorizontalGroup>
          )}
        </HorizontalGroup>
        <HorizontalGroup>
          <PluginLink className={cx('hover-button')} target="_blank" query={{ page: 'users', id: data.pk }}>
            <IconButton
              tooltip="Open user profile in new tab"
              style={{ color: 'var(--always-gray)' }}
              name="external-link-alt"
            />
          </PluginLink>
          <IconButton
            tooltip="Remove responder"
            className={cx('hover-button')}
            name="trash-alt"
            onClick={handleDelete}
          />
        </HorizontalGroup>
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
          <Text className={cx('responder-name')}>{data.name}</Text>
          <Text type="secondary">by</Text>
          <Select
            className={cx('select')}
            width="auto"
            isSearchable={false}
            value={Number(important)}
            options={[
              {
                value: 0,
                label: 'Default',
                description: 'Use "Default notifications" from users personal settings',
              },
              {
                value: 1,
                label: 'Important',
                description: 'Use "Important notifications" from users personal settings',
              },
            ]}
            onChange={onImportantChange}
          />
          <Text type="secondary">notification policies</Text>
        </HorizontalGroup>
        <HorizontalGroup>
          <PluginLink className={cx('hover-button')} target="_blank" query={{ page: 'schedules', id: data.id }}>
            <IconButton
              tooltip="Open schedule in new tab"
              style={{ color: 'var(--always-gray)' }}
              name="external-link-alt"
            />
          </PluginLink>
          <IconButton
            className={cx('hover-button')}
            tooltip="Remove responder"
            name="trash-alt"
            onClick={handleDelete}
          />
        </HorizontalGroup>
      </HorizontalGroup>
    </li>
  );
};

export default EscalationVariants;
