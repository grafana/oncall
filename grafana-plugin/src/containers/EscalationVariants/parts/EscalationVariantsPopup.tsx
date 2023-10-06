import React, { useState, useCallback, useEffect, useRef } from 'react';

import { HorizontalGroup, Icon, Input, RadioButtonGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { ColumnsType } from 'rc-table/lib/interface';

import Avatar from 'components/Avatar/Avatar';
import GTable from 'components/GTable/GTable';
import Text from 'components/Text/Text';
import styles from 'containers/EscalationVariants/EscalationVariants.module.scss';
import {
  TeamResponder,
  UserAvailability,
  UserResponders,
} from 'containers/EscalationVariants/EscalationVariants.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';
import { useDebouncedCallback, useOnClickOutside } from 'utils/hooks';

type EscalationVariantsPopupProps = {
  selectedTeamResponder: TeamResponder;
  selectedUserResponders: UserResponders;
  addSelectedUser: (user: User) => void;
  updateSelectedTeam: (team: GrafanaTeam) => void;

  setShowEscalationVariants: (value: boolean) => void;
  setShowUserWarningModal: (value: boolean) => void;
  setUserAvailability: (data: UserAvailability) => void;
};

const cx = cn.bind(styles);

enum TabOptions {
  Teams = 'teams',
  Users = 'users',
}

// TODO: filter out 'No team'
const EscalationVariantsPopup = observer((props: EscalationVariantsPopupProps) => {
  const {
    selectedTeamResponder,
    selectedUserResponders,
    setShowEscalationVariants,
    addSelectedUser,
    updateSelectedTeam,
    setShowUserWarningModal,
    setUserAvailability,
  } = props;

  const { grafanaTeamStore, userStore } = useStore();

  const [activeOption, setActiveOption] = useState<TabOptions>(TabOptions.Teams);
  const [searchTerm, setSearchTerm] = useState('');

  const ref = useRef();
  const teamSearchResults = grafanaTeamStore.getSearchResult();
  const userSearchResults = userStore.getSearchResult().results || [];

  const usersCurrentlyOnCall = userSearchResults.filter(({ is_currently_oncall }) => is_currently_oncall);
  const usersNotCurrentlyOnCall = userSearchResults.filter(({ is_currently_oncall }) => !is_currently_oncall);

  useOnClickOutside(ref, () => {
    setShowEscalationVariants(false);
  });

  const handleSetSearchTerm = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearchTerm(e.target.value);
    },
    [setSearchTerm]
  );

  const handleOptionChange = useCallback(
    (option: TabOptions) => {
      setActiveOption(option);
    },
    [setActiveOption]
  );

  const addUserResponders = useCallback(
    async (user: User) => {
      const userAvailability = await userStore.checkUserAvailability(user.pk);

      addSelectedUser(user);
      setUserAvailability(userAvailability);
      setShowUserWarningModal(true);

      setShowEscalationVariants(false);
    },
    [userStore, addSelectedUser, setUserAvailability, setShowUserWarningModal, setShowEscalationVariants]
  );

  const addTeamResponder = useCallback(
    (team: GrafanaTeam) => {
      setShowEscalationVariants(false);
      updateSelectedTeam(team);
    },
    [setShowEscalationVariants, updateSelectedTeam]
  );

  const handleSearchTermChange = useDebouncedCallback(() => {
    if (activeOption === TabOptions.Teams) {
      grafanaTeamStore.updateItems(searchTerm, false);
    } else {
      userStore.updateItems(searchTerm);
    }
  }, 500);

  useEffect(handleSearchTermChange, [searchTerm, activeOption]);

  const teamIsSelected = useCallback(
    (team: GrafanaTeam) => selectedTeamResponder?.data?.id === team.id,
    [selectedTeamResponder]
  );
  const userIsSelected = useCallback(
    (user: User) => selectedUserResponders.some((userResponder) => userResponder.data.pk === user.pk),
    [selectedUserResponders]
  );

  const teamColumns: ColumnsType<GrafanaTeam> = [
    {
      width: 300,
      render: (team: GrafanaTeam) => {
        const { avatar_url, name, number_of_users_currently_oncall } = team;
        const disabled = teamIsSelected(team);

        return (
          <div onClick={() => (disabled ? undefined : addTeamResponder(team))} className={cx('responder-item')}>
            <HorizontalGroup>
              <Avatar size="small" src={avatar_url} />
              <Text type={disabled ? 'disabled' : undefined}>{name}</Text>
              {number_of_users_currently_oncall > 0 && (
                <Text>
                  {number_of_users_currently_oncall} user{number_of_users_currently_oncall > 1 ? 's' : ''} on-call
                </Text>
              )}
            </HorizontalGroup>
          </div>
        );
      },
      key: 'Title',
    },
    {
      width: 40,
      render: (team: GrafanaTeam) => (teamIsSelected(team) ? <Icon name="check" /> : null),
      key: 'Checked',
    },
  ];

  const userColumns: ColumnsType<User> = [
    {
      width: 300,
      render: (user: User) => {
        const { avatar, name, username, teams } = user;
        const disabled = userIsSelected(user);

        return (
          <div onClick={() => (disabled ? undefined : addUserResponders(user))} className={cx('responder-item')}>
            <HorizontalGroup>
              <Avatar size="small" src={avatar} />
              <Text type={disabled ? 'disabled' : undefined}>{name || username}</Text>
              {teams.length > 0 && <Text>{teams.map(({ name }) => name).join(', ')}</Text>}
            </HorizontalGroup>
          </div>
        );
      },
      key: 'username',
    },
    {
      width: 40,
      render: (user: User) => (userIsSelected(user) ? <Icon name="check" /> : null),
      key: 'Checked',
    },
  ];

  return (
    <div ref={ref} className={cx('escalation-variants-dropdown')}>
      <Input
        suffix={<Icon name="search" />}
        key="search"
        className={cx('responders-filters')}
        value={searchTerm}
        placeholder="Search"
        // @ts-ignore
        width={'unset'}
        onChange={handleSetSearchTerm}
      />
      <RadioButtonGroup
        options={[
          { value: TabOptions.Teams, label: 'Teams' },
          { value: TabOptions.Users, label: 'Users' },
        ]}
        className={cx('radio-buttons')}
        value={activeOption}
        onChange={handleOptionChange}
        fullWidth
      />
      {activeOption === TabOptions.Teams && (
        <GTable<GrafanaTeam>
          emptyText={teamSearchResults ? 'No teams found' : 'Loading...'}
          rowKey="id"
          columns={teamColumns}
          data={teamSearchResults}
          className={cx('table')}
          showHeader={false}
        />
      )}
      {activeOption === TabOptions.Users && (
        <>
          {usersCurrentlyOnCall.length > 0 && (
            <>
              <p>On-call now</p>
              <GTable<User>
                emptyText={usersCurrentlyOnCall ? 'No users found' : 'Loading...'}
                rowKey="id"
                columns={userColumns}
                data={usersCurrentlyOnCall}
                className={cx('table')}
                showHeader={false}
              />
            </>
          )}
          {usersNotCurrentlyOnCall.length > 0 && (
            <>
              <p>Not on-call</p>
              <GTable<User>
                emptyText={usersNotCurrentlyOnCall ? 'No users found' : 'Loading...'}
                rowKey="id"
                columns={userColumns}
                data={usersNotCurrentlyOnCall}
                className={cx('table')}
                showHeader={false}
              />
            </>
          )}
        </>
      )}
    </div>
  );
});

export default EscalationVariantsPopup;
