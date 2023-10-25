import React, { useState, useContext, useCallback, useMemo } from 'react';

import { SelectableValue } from '@grafana/data';
import { HorizontalGroup, Button, Modal, Alert, VerticalGroup, Icon } from '@grafana/ui';
import cn from 'classnames/bind';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';

import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Alert as AlertType } from 'models/alertgroup/alertgroup.types';
import { getTimezone } from 'models/user/user.helpers';
import { User } from 'models/user/user.types';
import { DirectPagingContext } from 'state/context/directPaging';
import { UserActions } from 'utils/authorization';

import styles from './AddResponders.module.scss';
import { NotificationPolicyValue, UserResponder as UserResponderType } from './AddResponders.types';
import AddRespondersPopup from './parts/AddRespondersPopup/AddRespondersPopup';
import NotificationPoliciesSelect from './parts/NotificationPoliciesSelect/NotificationPoliciesSelect';
import TeamResponder from './parts/TeamResponder/TeamResponder';
import UserResponder from './parts/UserResponder/UserResponder';

const cx = cn.bind(styles);

type Props = {
  mode: 'create' | 'update';
  hideAddResponderButton?: boolean;
  existingPagedUsers?: AlertType['paged_users'];
  onAddNewParticipant?: (responder: Omit<UserResponderType, 'type'>) => Promise<void>;
  generateRemovePreviouslyPagedUserCallback?: (userId: string) => () => Promise<void>;
};

const LearnMoreAboutNotificationPoliciesLink: React.FC = () => (
  <a
    className={cx('learn-more-link')}
    href="https://grafana.com/docs/oncall/latest/notify/#configure-user-notification-policies"
    target="_blank"
    rel="noreferrer"
  >
    <Text type="link">
      <HorizontalGroup spacing="xs">
        Learn more
        <Icon name="external-link-alt" />
      </HorizontalGroup>
    </Text>
  </a>
);

const AddResponders = observer(
  ({
    mode,
    hideAddResponderButton,
    existingPagedUsers = [],
    onAddNewParticipant,
    generateRemovePreviouslyPagedUserCallback,
  }: Props) => {
    const {
      addUserToSelectedUsers,
      selectedTeamResponder,
      selectedUserResponders,
      resetSelectedTeam,
      generateRemoveSelectedUserHandler,
      generateUpdateSelectedUserImportantStatusHandler,
    } = useContext(DirectPagingContext);

    const currentMoment = useMemo(() => dayjs(), []);
    const isCreateMode = mode === 'create';

    const [currentlyConsideredUser, setCurrentlyConsideredUser] = useState<User>(null);
    const [currentlyConsideredUserNotificationPolicy, setCurrentlyConsideredUserNotificationPolicy] =
      useState<NotificationPolicyValue>(NotificationPolicyValue.Default);

    const [popupIsVisible, setPopupIsVisible] = useState(false);
    const [showUserConfirmationModal, setShowUserConfirmationModal] = useState(false);

    const onChangeCurrentlyConsideredUserNotificationPolicy = useCallback(
      ({ value }: SelectableValue<number>) => {
        setCurrentlyConsideredUserNotificationPolicy(value);
      },
      [setCurrentlyConsideredUserNotificationPolicy]
    );

    const closeUserConfirmationModal = useCallback(
      () => setShowUserConfirmationModal(false),
      [setShowUserConfirmationModal]
    );

    const confirmCurrentlyConsideredUser = useCallback(async () => {
      /**
       * if we're in create mode (ie. manually creating an alert group),
       * we need to add the user to the array of selected users
       * otherwise, as soon as the modal is confirmed, we add the user to the pre-existing list of "paged users"
       * for the alert group
       */
      if (isCreateMode) {
        addUserToSelectedUsers(currentlyConsideredUser);
      } else {
        await onAddNewParticipant({
          important: Boolean(currentlyConsideredUserNotificationPolicy),
          data: currentlyConsideredUser,
        });
      }

      closeUserConfirmationModal();
    }, [
      isCreateMode,
      addUserToSelectedUsers,
      currentlyConsideredUser,
      currentlyConsideredUserNotificationPolicy,
      closeUserConfirmationModal,
    ]);

    return (
      <>
        <div className={cx('body')}>
          <Block bordered>
            <HorizontalGroup justify="space-between">
              <Text.Title type="primary" level={4}>
                Participants
              </Text.Title>
              {!hideAddResponderButton && (
                <WithPermissionControlTooltip userAction={UserActions.AlertGroupsDirectPaging}>
                  <Button
                    variant="secondary"
                    icon="plus"
                    onClick={() => {
                      setPopupIsVisible(true);
                    }}
                  >
                    {isCreateMode ? 'Invite' : 'Add'}
                  </Button>
                </WithPermissionControlTooltip>
              )}
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
                  {selectedUserResponders.length > 0 && (
                    <Alert
                      severity="info"
                      title={
                        (
                          <Text type="primary">
                            <LearnMoreAboutNotificationPoliciesLink /> about Default vs Important user personal
                            notification settings
                          </Text>
                        ) as any
                      }
                    />
                  )}
                </ul>
              </>
            )}
          </Block>
          <AddRespondersPopup
            mode={mode}
            visible={popupIsVisible}
            setVisible={setPopupIsVisible}
            existingPagedUsers={existingPagedUsers}
            setCurrentlyConsideredUser={setCurrentlyConsideredUser}
            setShowUserConfirmationModal={setShowUserConfirmationModal}
          />
        </div>
        {showUserConfirmationModal && (
          <Modal
            isOpen
            title="Confirm Participant Invitation"
            onDismiss={closeUserConfirmationModal}
            className={cx('confirm-participant-invitation-modal')}
          >
            <VerticalGroup spacing="md">
              {!isCreateMode && (
                <div>
                  <Text>
                    <Text strong>{currentlyConsideredUser.name || currentlyConsideredUser.username}</Text> (local time{' '}
                    {currentMoment.tz(getTimezone(currentlyConsideredUser)).format('HH:mm')}) will be notified using
                  </Text>
                  <div className={cx('confirm-participant-invitation-modal-select')}>
                    <NotificationPoliciesSelect
                      important={Boolean(currentlyConsideredUserNotificationPolicy)}
                      onChange={onChangeCurrentlyConsideredUserNotificationPolicy}
                    />
                  </div>
                  <Text>notification settings. </Text>
                  <LearnMoreAboutNotificationPoliciesLink />
                </div>
              )}
              {!currentlyConsideredUser.is_currently_oncall && (
                <Alert
                  severity="warning"
                  title="This user is not currently on-call. We don't recommend to page users outside on-call hours."
                />
              )}
              <HorizontalGroup justify="flex-end">
                <Button variant="secondary" onClick={closeUserConfirmationModal}>
                  Cancel
                </Button>
                <Button variant="primary" onClick={confirmCurrentlyConsideredUser}>
                  Confirm
                </Button>
              </HorizontalGroup>
            </VerticalGroup>
          </Modal>
        )}
      </>
    );
  }
);

export default AddResponders;
