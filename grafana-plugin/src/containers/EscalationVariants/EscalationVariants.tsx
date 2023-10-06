import React, { useState, useCallback } from 'react';

import { SelectableValue } from '@grafana/data';
import { HorizontalGroup, Button } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

// import Avatar from 'components/Avatar/Avatar';
import Block from 'components/GBlock/Block';
// import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
// import UserWarning from 'containers/UserWarningModal/UserWarning';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { User } from 'models/user/user.types';
import { UserActions } from 'utils/authorization';

// import { deduplicate } from './EscalationVariants.helpers';
import styles from './EscalationVariants.module.scss';
// import { ResponderType, UserAvailability } from './EscalationVariants.types';
import {
  UserResponders,
  UserAvailability,
  ResponderType,
  TeamResponder as TeamResponderType,
} from './EscalationVariants.types';
import EscalationVariantsPopup from './parts/EscalationVariantsPopup';
import TeamResponder from './parts/TeamResponder';
import UserResponder from './parts/UserResponder';

const cx = cn.bind(styles);

type EscalationVariantsProps = {
  hideSelected?: boolean;
};

const EscalationVariants = observer(({ hideSelected = false }: EscalationVariantsProps) => {
  const [showEscalationVariants, setShowEscalationVariants] = useState(false);

  const [_showUserWarningModal, setShowUserWarningModal] = useState(false);

  const [selectedTeamResponder, setSelectedTeamResponder] = useState<TeamResponderType>(null);
  const [selectedUserResponders, setSelectedUserResponders] = useState<UserResponders>([]);

  const [_userAvailability, setUserAvailability] = useState<UserAvailability | undefined>(undefined);

  const addUserToSelectedUsers = useCallback(
    (user: User) => {
      setSelectedUserResponders((users) => [
        ...users,
        {
          type: ResponderType.User,
          data: user,
          important: false,
        },
      ]);
    },
    [setSelectedUserResponders]
  );

  const updateSelectedTeam = useCallback(
    (team: GrafanaTeam) => {
      setSelectedTeamResponder({
        type: ResponderType.Team,
        data: team,
        important: false,
      });
    },
    [setSelectedTeamResponder]
  );

  const getUserResponderImportantChangeHandler = (index: number) => {
    return ({ value: important }: SelectableValue<number>) => {
      setSelectedUserResponders((selectedUsers) => [
        ...selectedUsers.slice(0, index),
        {
          ...selectedUsers[index],
          important: Boolean(important),
        },
        ...selectedUsers.slice(index + 1),
      ]);
    };
  };

  const getUserResponderDeleteHandler = (index: number) => {
    return () => {
      setSelectedUserResponders((selectedUsers) => [
        ...selectedUsers.slice(0, index),
        ...selectedUsers.slice(index + 1),
      ]);
    };
  };

  const teamResponderImportantChangeHandler = useCallback(
    ({ value: important }: SelectableValue<number>) => {
      setSelectedTeamResponder({
        ...selectedTeamResponder,
        important: Boolean(important),
      });
    },
    [setSelectedTeamResponder]
  );

  const teamResponderDeleteHandler = useCallback(() => {
    setSelectedTeamResponder(null);
  }, [setSelectedTeamResponder]);

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
                Invite
              </Button>
            </WithPermissionControlTooltip>
          </HorizontalGroup>
          {!hideSelected && (selectedTeamResponder || selectedUserResponders.length > 0) && (
            <>
              <ul className={cx('responders-list')}>
                {selectedTeamResponder && (
                  <TeamResponder
                    onImportantChange={teamResponderImportantChangeHandler}
                    handleDelete={teamResponderDeleteHandler}
                    {...selectedTeamResponder}
                  />
                )}
                {selectedUserResponders.map((responder, index) => (
                  <UserResponder
                    key={responder.data.pk}
                    onImportantChange={getUserResponderImportantChangeHandler(index)}
                    handleDelete={getUserResponderDeleteHandler(index)}
                    {...responder}
                  />
                ))}
              </ul>
            </>
          )}
        </Block>
        {showEscalationVariants && (
          <EscalationVariantsPopup
            selectedTeamResponder={selectedTeamResponder}
            selectedUserResponders={selectedUserResponders}
            addSelectedUser={addUserToSelectedUsers}
            updateSelectedTeam={updateSelectedTeam}
            setShowEscalationVariants={setShowEscalationVariants}
            setShowUserWarningModal={setShowUserWarningModal}
            setUserAvailability={setUserAvailability}
          />
        )}
      </div>
      {/* {showUserWarningModal && (
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
        )} */}
    </>
  );
});

export default EscalationVariants;
