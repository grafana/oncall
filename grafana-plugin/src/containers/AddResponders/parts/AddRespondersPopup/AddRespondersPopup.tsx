import React, { useState, useCallback, useEffect, useRef, FC } from 'react';

import { Alert, HorizontalGroup, Icon, Input, RadioButtonGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { ColumnsType } from 'rc-table/lib/interface';

import Avatar from 'components/Avatar/Avatar';
import GTable from 'components/GTable/GTable';
import Text from 'components/Text/Text';
import { Alert as AlertType } from 'models/alertgroup/alertgroup.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { UserCurrentlyOnCall } from 'models/user/user.types';
import { useStore } from 'state/useStore';
import { useDebouncedCallback, useOnClickOutside } from 'utils/hooks';

import styles from './AddRespondersPopup.module.scss';

type Props = {
  mode: 'create' | 'update';
  visible: boolean;
  setVisible: (value: boolean) => void;

  setCurrentlyConsideredUser: (user: UserCurrentlyOnCall) => void;
  setShowUserConfirmationModal: (value: boolean) => void;

  existingPagedUsers?: AlertType['paged_users'];
};

const cx = cn.bind(styles);

enum TabOptions {
  Teams = 'teams',
  Users = 'users',
}

/**
 * TODO: properly filter out 'No team'. Right now it shows up on first render and then shortly thereafter the component
 * re-renders with 'No team' filtered out
 *
 * TODO: properly fetch/show loading state when fetching users. Right now it shows an empty list on the initial network
 * request, we can probably have a better experience here
 */
const AddRespondersPopup = observer(
  ({
    mode,
    visible,
    setVisible,
    existingPagedUsers = [],
    setCurrentlyConsideredUser,
    setShowUserConfirmationModal,
  }: Props) => {
    const { directPagingStore, grafanaTeamStore, userStore } = useStore();
    const { selectedTeamResponder, selectedUserResponders } = directPagingStore;

    const isCreateMode = mode === 'create';

    const [activeOption, setActiveOption] = useState<TabOptions>(isCreateMode ? TabOptions.Teams : TabOptions.Users);
    const [userSearchResults, setUserSearchResults] = useState<UserCurrentlyOnCall[]>([]);
    const [searchTerm, setSearchTerm] = useState('');

    const ref = useRef();
    const teamSearchResults = grafanaTeamStore.getSearchResult();

    /**
     * in the context where some user(s) have already been paged (ex. on a direct paging generated
     * alert group detail page), we should filter out the search results to not include these users
     */
    if (existingPagedUsers.length > 0) {
      const existingPagedUserIds = existingPagedUsers.map(({ pk }) => pk);
      setUserSearchResults(userSearchResults.filter(({ pk }) => !existingPagedUserIds.includes(pk)));
    }

    const usersCurrentlyOnCall = userSearchResults.filter(({ is_currently_oncall }) => is_currently_oncall);
    const usersNotCurrentlyOnCall = userSearchResults.filter(({ is_currently_oncall }) => !is_currently_oncall);

    useOnClickOutside(ref, () => {
      setVisible(false);
    });

    const handleSetSearchTerm = useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchTerm(e.target.value);
      },
      [setSearchTerm]
    );

    const onClickUser = useCallback(
      async (user: UserCurrentlyOnCall) => {
        if (isCreateMode && user.is_currently_oncall) {
          directPagingStore.addUserToSelectedUsers(user);
        } else {
          setCurrentlyConsideredUser(user);
          setShowUserConfirmationModal(true);
        }
        setVisible(false);
      },
      [isCreateMode, userStore, directPagingStore, setShowUserConfirmationModal, setVisible]
    );

    const addTeamResponder = useCallback(
      (team: GrafanaTeam) => {
        setVisible(false);
        directPagingStore.updateSelectedTeam(team);

        /**
         * can't select more than one team so we mind as well auto-switch the selected tab
         * to the users section in case the user wants to come back and user(s)
         */
        setActiveOption(TabOptions.Users);
      },
      [setVisible, directPagingStore, setActiveOption]
    );

    const searchForUsers = useCallback(async () => {
      const userResults = await userStore.search<UserCurrentlyOnCall>({ searchTerm, is_currently_oncall: 'all' });
      setUserSearchResults(userResults.results);
    }, []);

    const handleSearchTermChange = useDebouncedCallback(async () => {
      // TODO: would be nice to add a loading state here...
      if (isCreateMode && activeOption === TabOptions.Teams) {
        grafanaTeamStore.updateItems(searchTerm, false, true, false);
      } else {
        await searchForUsers();
      }
    }, 500);

    useEffect(handleSearchTermChange, [searchTerm, activeOption]);

    /**
     * populate the initial user search results before the user jumps over to the users tab
     * should provide a slightly nicer UX
     */
    useEffect(() => {
      searchForUsers();
    }, []);

    const userIsSelected = useCallback(
      (user: UserCurrentlyOnCall) => selectedUserResponders.some((userResponder) => userResponder.data.pk === user.pk),
      [selectedUserResponders]
    );

    const teamColumns: ColumnsType<GrafanaTeam> = [
      // TODO: how to make the rows span full width properly?
      {
        width: 300,
        render: (team: GrafanaTeam) => {
          const { avatar_url, name, number_of_users_currently_oncall } = team;

          return (
            <div onClick={() => addTeamResponder(team)} className={cx('responder-item')}>
              <HorizontalGroup justify="space-between">
                <HorizontalGroup>
                  <Avatar size="small" src={avatar_url} />
                  <Text>{name}</Text>
                </HorizontalGroup>
                {number_of_users_currently_oncall > 0 && (
                  <Text type="secondary">
                    {number_of_users_currently_oncall} user{number_of_users_currently_oncall > 1 ? 's' : ''} on-call
                  </Text>
                )}
              </HorizontalGroup>
            </div>
          );
        },
        key: 'Title',
      },
    ];

    const userColumns: ColumnsType<UserCurrentlyOnCall> = [
      // TODO: how to make the rows span full width properly?
      {
        width: 300,
        render: (user: UserCurrentlyOnCall) => {
          const { avatar, name, username, teams } = user;
          const disabled = userIsSelected(user);

          return (
            <div onClick={() => (disabled ? undefined : onClickUser(user))} className={cx('responder-item')}>
              <HorizontalGroup justify="space-between">
                <HorizontalGroup>
                  <Avatar size="small" src={avatar} />
                  <Text type={disabled ? 'disabled' : undefined}>{name || username}</Text>
                </HorizontalGroup>
                {teams?.length > 0 && <Text type="secondary">{teams.map(({ name }) => name).join(', ')}</Text>}
              </HorizontalGroup>
            </div>
          );
        },
        key: 'username',
      },
      {
        width: 40,
        render: (user: UserCurrentlyOnCall) => (userIsSelected(user) ? <Icon name="check" /> : null),
        key: 'Checked',
      },
    ];

    const UserResultsSection: FC<{ header: string; users: UserCurrentlyOnCall[] }> = ({ header, users }) =>
      users.length > 0 && (
        <>
          <Text type="secondary" className={cx('user-results-section-header')}>
            {header}
          </Text>
          <GTable<UserCurrentlyOnCall>
            emptyText={users ? 'No users found' : 'Loading...'}
            rowKey="pk"
            columns={userColumns}
            data={users}
            className={cx('table')}
            showHeader={false}
          />
        </>
      );

    return (
      visible && (
        <div data-testid="add-responders-popup" ref={ref} className={cx('add-responders-dropdown')}>
          <Input
            suffix={<Icon name="search" />}
            key="search"
            className={cx('responders-filters')}
            data-testid="add-responders-search-input"
            value={searchTerm}
            placeholder="Search"
            // @ts-ignore
            width={'unset'}
            onChange={handleSetSearchTerm}
          />
          {isCreateMode && (
            <RadioButtonGroup
              options={[
                { value: TabOptions.Teams, label: 'Teams' },
                { value: TabOptions.Users, label: 'Users' },
              ]}
              className={cx('radio-buttons')}
              value={activeOption}
              onChange={setActiveOption}
              fullWidth
            />
          )}
          {activeOption === TabOptions.Teams && (
            <>
              {selectedTeamResponder ? (
                <Alert
                  severity="info"
                  title="You can add only one team per escalation. Please remove the existing team before adding a new one."
                />
              ) : (
                <>
                  <Alert
                    className={cx('team-direct-paging-info-alert')}
                    severity="info"
                    title={
                      (
                        <Text type="primary">
                          You can only page teams which have a Direct Paging integration that is configured.{' '}
                          <a
                            className={cx('learn-more-link')}
                            href="https://grafana.com/docs/oncall/latest/integrations/manual/#set-up-direct-paging-for-a-team"
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
                        </Text>
                      ) as any
                    }
                  />
                  <GTable<GrafanaTeam>
                    emptyText={teamSearchResults ? 'No teams found' : 'Loading...'}
                    rowKey="id"
                    columns={teamColumns}
                    data={teamSearchResults}
                    className={cx('table')}
                    showHeader={false}
                  />
                </>
              )}
            </>
          )}
          {activeOption === TabOptions.Users && (
            <>
              <UserResultsSection header="On-call now" users={usersCurrentlyOnCall} />
              <UserResultsSection header="Not on-call" users={usersNotCurrentlyOnCall} />
            </>
          )}
        </div>
      )
    );
  }
);

export default AddRespondersPopup;
