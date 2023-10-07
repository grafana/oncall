import React, { useState, useContext, useCallback, useMemo } from 'react';

import { SelectableValue } from '@grafana/data';
import { HorizontalGroup, Button, Modal } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

// import Avatar from 'components/Avatar/Avatar';
import Block from 'components/GBlock/Block';
// import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
// import UserWarning from 'containers/UserWarningModal/UserWarning';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { getTimezone } from 'models/user/user.helpers';
import { User } from 'models/user/user.types';
import { DirectPagingContext } from 'state/context/directPaging';
import { UserActions } from 'utils/authorization';

import styles from './EscalationVariants.module.scss';
// import { ResponderType, UserAvailability } from './EscalationVariants.types';
import { NotificationPolicyValue, UserAvailability } from './EscalationVariants.types';
import EscalationVariantsPopup from './parts/EscalationVariantsPopup';
import NotificationPoliciesSelect from './parts/NotificationPoliciesSelect';
import TeamResponder from './parts/TeamResponder';
import UserResponder from './parts/UserResponder';

const cx = cn.bind(styles);

type EscalationVariantsProps = {
  mode: 'create' | 'update';
  existingPagedUsers?: Alert['paged_users'];
  generateRemovePreviouslyPagedUserCallback?: (userId: string) => () => Promise<void>;
};

// TODO: rename this component...
const EscalationVariants = observer(
  ({ mode, existingPagedUsers = [], generateRemovePreviouslyPagedUserCallback }: EscalationVariantsProps) => {
    const {
      selectedTeamResponder,
      selectedUserResponders,
      updateSelectedTeam,
      updateSelectedTeamImportantStatus,
      generateRemoveSelectedUserHandler,
      generateUpdateSelectedUserImportantStatusHandler,
    } = useContext(DirectPagingContext);

    const currentMoment = useMemo(() => dayjs(), []);

    const [currentlyConsideredUser, setCurrentlyConsideredUser] = useState<User>(null);
    const [currentlyConsideredUserNotificationPolicy, setCurrentlyConsideredUserNotificationPolicy] =
      useState<NotificationPolicyValue>(NotificationPolicyValue.Default);

    const [showEscalationVariants, setShowEscalationVariants] = useState(false);
    const [showUserWarningModal, setShowUserWarningModal] = useState(false);
    const [_userAvailability, setUserAvailability] = useState<UserAvailability | undefined>(undefined);

    const onChangeCurrentlyConsideredUserNotificationPolicy = useCallback(
      ({ value }: SelectableValue<number>) => {
        setCurrentlyConsideredUserNotificationPolicy(value);
      },
      [setCurrentlyConsideredUserNotificationPolicy]
    );

    const confirmCurrentlyConsideredUser = useCallback(() => {
      console.log('yoooo');
    }, []);

    console.log('hellooooo', currentlyConsideredUser);

    const closeUserWarningModal = useCallback(() => setShowUserWarningModal(false), [showUserWarningModal]);

    return (
      <>
        <div className={cx('body')}>
          <Block bordered className={cx('block')}>
            <HorizontalGroup justify="space-between">
              <Text type="primary" size="medium">
                Participants
              </Text>
              <WithPermissionControlTooltip userAction={UserActions.AlertGroupsDirectPaging}>
                <Button
                  variant="secondary"
                  icon="plus"
                  onClick={() => {
                    setShowEscalationVariants(true);
                  }}
                >
                  {mode === 'create' ? 'Invite' : 'Add'}
                </Button>
              </WithPermissionControlTooltip>
            </HorizontalGroup>
            {(selectedTeamResponder || existingPagedUsers.length > 0 || selectedUserResponders.length > 0) && (
              <>
                <ul className={cx('responders-list')}>
                  {selectedTeamResponder && (
                    <TeamResponder
                      onImportantChange={updateSelectedTeamImportantStatus}
                      handleDelete={() => updateSelectedTeam(undefined)}
                      {...selectedTeamResponder}
                    />
                  )}
                  {existingPagedUsers.map((user) => (
                    <UserResponder
                      key={user.pk}
                      onImportantChange={() => {}}
                      disableNotificationPolicySelect
                      handleDelete={generateRemovePreviouslyPagedUserCallback(user.pk)}
                      important={user.important}
                      // TODO:
                      data={user as unknown as User}
                    />
                  ))}
                  {selectedUserResponders.map((responder, index) => (
                    <UserResponder
                      key={responder.data.pk}
                      onImportantChange={generateUpdateSelectedUserImportantStatusHandler(index)}
                      handleDelete={generateRemoveSelectedUserHandler(index)}
                      {...responder}
                    />
                  ))}
                </ul>
              </>
            )}
          </Block>
          {showEscalationVariants && (
            <EscalationVariantsPopup
              mode={mode}
              setCurrentlyConsideredUser={setCurrentlyConsideredUser}
              setShowUserWarningModal={setShowUserWarningModal}
              setShowEscalationVariants={setShowEscalationVariants}
              setUserAvailability={setUserAvailability}
            />
          )}
        </div>
        {showUserWarningModal && (
          <Modal
            isOpen
            title="Confirm Participant Invitation"
            onDismiss={closeUserWarningModal}
            className={cx('modal')}
          >
            {/* TODO: */}
            <Text>
              {currentlyConsideredUser.name || currentlyConsideredUser.username} (local time{' '}
              {currentMoment.tz(getTimezone(currentlyConsideredUser)).format('HH:mm')}) will be notified using
            </Text>
            <NotificationPoliciesSelect
              important={Boolean(currentlyConsideredUserNotificationPolicy)}
              onChange={onChangeCurrentlyConsideredUserNotificationPolicy}
            />
            <Text>notification settings. Learn more</Text>
            <HorizontalGroup justify="flex-end">
              <Button variant="secondary" onClick={closeUserWarningModal}>
                Cancel
              </Button>
              <Button variant="primary" onClick={confirmCurrentlyConsideredUser}>
                Confirm
              </Button>
            </HorizontalGroup>
          </Modal>
        )}
      </>
    );
  }
);

export default EscalationVariants;
