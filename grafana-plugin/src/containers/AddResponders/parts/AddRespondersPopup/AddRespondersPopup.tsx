import React, { useState, useCallback, useEffect, useRef, FC } from 'react';

import { Alert, HorizontalGroup, Icon, Input, LoadingPlaceholder, RadioButtonGroup } from '@grafana/ui';
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

    const [isInitialRender, setIsInitialRender] = useState<boolean>(true);
    const [searchLoading, setSearchLoading] = useState<boolean>(true);
    const [activeOption, setActiveOption] = useState<TabOptions>(isCreateMode ? TabOptions.Teams : TabOptions.Users);
    const [teamSearchResults, setTeamSearchResults] = useState<GrafanaTeam[]>([]);
    const [userSearchResults, setUserSearchResults] = useState<UserCurrentlyOnCall[]>([]);
    const [searchTerm, setSearchTerm] = useState('');

    const ref = useRef();
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
    }, [searchTerm]);

    const searchForTeams = useCallback(async () => {
      await grafanaTeamStore.updateItems(searchTerm, false, true, false);
      setTeamSearchResults(grafanaTeamStore.getSearchResult());
    }, [searchTerm]);

    const handleSearchTermChange = useDebouncedCallback(async () => {
      setSearchLoading(true);

      if (isInitialRender) {
        await searchForTeams();
        await searchForUsers();
        setIsInitialRender(false);
      } else if (isCreateMode && activeOption === TabOptions.Teams) {
        await searchForTeams();
      } else {
        await searchForUsers();
      }

      setSearchLoading(false);
    }, 500);

    const onChangeTab = useCallback((tab: TabOptions) => {
      /**
       * avoids a flicker where the results are shown momentarily before handleSearchTermChange
       * gets called which calls setSearchLoading(true);
       */
      setSearchLoading(true);
      setActiveOption(tab);
    }, []);

    useEffect(handleSearchTermChange, [searchTerm, activeOption]);

    /**
     * in the context where some user(s) have already been paged (ex. on a direct paging generated
     * alert group detail page), we should filter out the search results to not include these users
     */
    useEffect(() => {
      if (existingPagedUsers.length > 0) {
        const existingPagedUserIds = existingPagedUsers.map(({ pk }) => pk);
        setUserSearchResults((userSearchResults) =>
          userSearchResults.filter(({ pk }) => !existingPagedUserIds.includes(pk))
        );
      }
    }, [existingPagedUsers]);

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
                {/* TODO: we should add an elippsis and/or tooltip in the event that the user has a ton of teams */}
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
              onChange={onChangeTab}
              fullWidth
            />
          )}
          {searchLoading && <LoadingPlaceholder className={cx('loading-placeholder')} text="Loading..." />}
          {!searchLoading && activeOption === TabOptions.Teams && (
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
          {!searchLoading && activeOption === TabOptions.Users && (
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
