import React, { useState, useContext, useCallback, useMemo } from 'react';

import { SelectableValue } from '@grafana/data';
import { HorizontalGroup, Button, Modal, Alert } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

// import Avatar from 'components/Avatar/Avatar';
import Block from 'components/GBlock/Block';
// import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
// import UserWarning from 'containers/UserWarningModal/UserWarning';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Alert as AlertType } from 'models/alertgroup/alertgroup.types';
import { getTimezone } from 'models/user/user.helpers';
import { User } from 'models/user/user.types';
import { DirectPagingContext } from 'state/context/directPaging';
import { UserActions } from 'utils/authorization';

import styles from './AddResponders.module.scss';
// import { ResponderType, UserAvailability } from './AddResponders.types';
import { NotificationPolicyValue, UserAvailability, UserResponder as UserResponderType } from './AddResponders.types';
import AddRespondersPopup from './parts/AddRespondersPopup';
import NotificationPoliciesSelect from './parts/NotificationPoliciesSelect';
import TeamResponder from './parts/TeamResponder';
import UserResponder from './parts/UserResponder';

const cx = cn.bind(styles);

type Props = {
  mode: 'create' | 'update';
  existingPagedUsers?: AlertType['paged_users'];
  onAddNewParticipant?: (responder: Omit<UserResponderType, 'type'>) => Promise<void>;
  generateRemovePreviouslyPagedUserCallback?: (userId: string) => () => Promise<void>;
};

const AddResponders = observer(
  ({ mode, existingPagedUsers = [], onAddNewParticipant, generateRemovePreviouslyPagedUserCallback }: Props) => {
    const {
      selectedTeamResponder,
      selectedUserResponders,
      resetSelectedTeam,
      generateRemoveSelectedUserHandler,
      generateUpdateSelectedUserImportantStatusHandler,
    } = useContext(DirectPagingContext);

    const currentMoment = useMemo(() => dayjs(), []);

    const [currentlyConsideredUser, setCurrentlyConsideredUser] = useState<User>(null);
    const [currentlyConsideredUserNotificationPolicy, setCurrentlyConsideredUserNotificationPolicy] =
      useState<NotificationPolicyValue>(NotificationPolicyValue.Default);

    const [popupIsVisible, setPopupIsVisible] = useState(false);
    const [showUserWarningModal, setShowUserWarningModal] = useState(false);
    const [_userAvailability, setUserAvailability] = useState<UserAvailability | undefined>(undefined);

    const onChangeCurrentlyConsideredUserNotificationPolicy = useCallback(
      ({ value }: SelectableValue<number>) => {
        setCurrentlyConsideredUserNotificationPolicy(value);
      },
      [setCurrentlyConsideredUserNotificationPolicy]
    );

    const closeUserWarningModal = useCallback(() => setShowUserWarningModal(false), [showUserWarningModal]);

    const confirmCurrentlyConsideredUser = useCallback(async () => {
      await onAddNewParticipant({
        important: Boolean(currentlyConsideredUserNotificationPolicy),
        data: currentlyConsideredUser,
      });
      closeUserWarningModal();
    }, [currentlyConsideredUserNotificationPolicy, currentlyConsideredUser, closeUserWarningModal]);

    return (
      <>
        <div className={cx('body')}>
          <Block bordered>
            <HorizontalGroup justify="space-between">
              <Text type="primary" size="medium">
                Participants
              </Text>
              <WithPermissionControlTooltip userAction={UserActions.AlertGroupsDirectPaging}>
                <Button
                  variant="secondary"
                  icon="plus"
                  onClick={() => {
                    setPopupIsVisible(true);
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
                    <TeamResponder team={selectedTeamResponder} handleDelete={resetSelectedTeam} />
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
                  {/* TODO: where should this link to? */}
                  {selectedUserResponders.length > 0 && (
                    <Alert
                      severity="info"
                      title="Learn more about user's Default and Important personal notification settings"
                    />
                  )}
                </ul>
              </>
            )}
          </Block>
          {/* TODO: how to (properly) get this to "float" right when it's open? */}
          <AddRespondersPopup
            mode={mode}
            visible={popupIsVisible}
            setVisible={setPopupIsVisible}
            existingPagedUsers={existingPagedUsers}
            setCurrentlyConsideredUser={setCurrentlyConsideredUser}
            setShowUserWarningModal={setShowUserWarningModal}
            setUserAvailability={setUserAvailability}
          />
        </div>
        {showUserWarningModal && (
          <Modal
            isOpen
            title="Confirm Participant Invitation"
            onDismiss={closeUserWarningModal}
            className={cx('modal')}
          >
            {/* TODO: finish styling this */}
            <Text>
              {currentlyConsideredUser.name || currentlyConsideredUser.username} (local time{' '}
              {currentMoment.tz(getTimezone(currentlyConsideredUser)).format('HH:mm')}) will be notified using
            </Text>
            <NotificationPoliciesSelect
              important={Boolean(currentlyConsideredUserNotificationPolicy)}
              onChange={onChangeCurrentlyConsideredUserNotificationPolicy}
            />
            {/* TODO: where should 'Learn more' link to? */}
            <Text>notification settings. Learn more</Text>
            {!currentlyConsideredUser.is_currently_oncall && (
              <Alert
                severity="warning"
                title="This user is not currently on-call. We don't recommend to page users outside on-call hours."
              />
            )}
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

export default AddResponders;
