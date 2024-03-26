import React, { useState, useCallback, useEffect, useRef, FC } from 'react';

import { Alert, HorizontalGroup, Icon, Input, LoadingPlaceholder, RadioButtonGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { ColumnsType } from 'rc-table/lib/interface';

import { Avatar } from 'components/Avatar/Avatar';
import { GTable } from 'components/GTable/GTable';
import { Text } from 'components/Text/Text';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { UserHelper } from 'models/user/user.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';
import { useDebouncedCallback, useOnClickOutside } from 'utils/hooks';

import styles from './AddRespondersPopup.module.scss';

type Props = {
  mode: 'create' | 'update';
  visible: boolean;
  setVisible: (value: boolean) => void;

  setCurrentlyConsideredUser: (user: ApiSchemas['UserIsCurrentlyOnCall']) => void;
  setShowUserConfirmationModal: (value: boolean) => void;

  existingPagedUsers?: ApiSchemas['AlertGroup']['paged_users'];
};

const cx = cn.bind(styles);

enum TabOptions {
  Teams = 'teams',
  Users = 'users',
}

export const AddRespondersPopup = observer(
  ({
    mode,
    visible,
    setVisible,
    existingPagedUsers = [],
    setCurrentlyConsideredUser,
    setShowUserConfirmationModal,
  }: Props) => {
    const { directPagingStore, grafanaTeamStore } = useStore();
    const { selectedTeamResponder, selectedUserResponders } = directPagingStore;

    const isCreateMode = mode === 'create';

    const [searchLoading, setSearchLoading] = useState(true);
    const [activeOption, setActiveOption] = useState<TabOptions>(isCreateMode ? TabOptions.Teams : TabOptions.Users);
    const [teamSearchResults, setTeamSearchResults] = useState<GrafanaTeam[]>([]);
    const [onCallUserSearchResults, setOnCallUserSearchResults] = useState<Array<ApiSchemas['UserIsCurrentlyOnCall']>>(
      []
    );
    const [notOnCallUserSearchResults, setNotOnCallUserSearchResults] = useState<
      Array<ApiSchemas['UserIsCurrentlyOnCall']>
    >([]);
    const [searchTerm, setSearchTerm] = useState('');

    const ref = useRef();

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
      async (user: ApiSchemas['UserIsCurrentlyOnCall']) => {
        if (isCreateMode && user.is_currently_oncall) {
          directPagingStore.addUserToSelectedUsers(user);
        } else {
          setCurrentlyConsideredUser(user);
          setShowUserConfirmationModal(true);
        }
        setVisible(false);
      },
      [isCreateMode, setShowUserConfirmationModal, setVisible]
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
      const _search = async (is_currently_oncall: boolean) => {
        const response = await UserHelper.search({
          searchTerm,
          is_currently_oncall,
        });
        return response.results;
      };

      const [onCallUserSearchResults, notOnCallUserSearchResults] = await Promise.all([_search(true), _search(false)]);

      setOnCallUserSearchResults(onCallUserSearchResults as Array<ApiSchemas['UserIsCurrentlyOnCall']>);
      setNotOnCallUserSearchResults(notOnCallUserSearchResults as Array<ApiSchemas['UserIsCurrentlyOnCall']>);
    }, [searchTerm]);

    const searchForTeams = useCallback(async () => {
      await grafanaTeamStore.updateItems(searchTerm, false, true, false);
      setTeamSearchResults(grafanaTeamStore.getSearchResult());
    }, [searchTerm]);

    const handleSearchTermChange = useDebouncedCallback(async () => {
      setSearchLoading(true);

      if (isCreateMode && activeOption === TabOptions.Teams) {
        await searchForTeams();
      } else {
        await searchForUsers();
      }

      setSearchLoading(false);
    }, 500);

    const onChangeTab = useCallback(
      async (tab: TabOptions) => {
        /**
         * there's no need to trigger a new search request when the user changes tabs if they don't have a
         * search term
         */
        if (searchTerm) {
          setSearchLoading(true);

          if (activeOption === TabOptions.Teams) {
            await searchForTeams();
          } else {
            await searchForUsers();
          }

          setSearchLoading(false);
        }

        setActiveOption(tab);
      },
      [searchTerm]
    );

    useEffect(handleSearchTermChange, [searchTerm]);

    /**
     * in the context where some user(s) have already been paged (ex. on a direct paging generated
     * alert group detail page), we should filter out the search results to not include these users
     */
    useEffect(() => {
      if (existingPagedUsers.length > 0) {
        const existingPagedUserIds = existingPagedUsers.map(({ pk }) => pk);

        const _filterUsers = (users: Array<ApiSchemas['UserIsCurrentlyOnCall']>) =>
          users.filter(({ pk }) => !existingPagedUserIds.includes(pk));

        setOnCallUserSearchResults(_filterUsers);
        setNotOnCallUserSearchResults(_filterUsers);
      }
    }, [existingPagedUsers]);

    /**
     * pre-populate the users and teams search results so that when the user opens AddRespondersPopup it is already
     * populated with data (nicer UX)
     */
    useEffect(() => {
      (async () => {
        /**
         * teams are not relevant when the component is rendered in "update" mode so we skip fetching teams here
         */
        if (isCreateMode) {
          await searchForTeams();
        }

        await searchForUsers();
        setSearchLoading(false);
      })();
    }, []);

    const userIsSelected = useCallback(
      (user: ApiSchemas['UserIsCurrentlyOnCall']) =>
        selectedUserResponders.some((userResponder) => userResponder.data.pk === user.pk),
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

    const userColumns: ColumnsType<ApiSchemas['UserIsCurrentlyOnCall']> = [
      // TODO: how to make the rows span full width properly?
      {
        width: 300,
        render: (user: ApiSchemas['UserIsCurrentlyOnCall']) => {
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
        render: (user: ApiSchemas['UserIsCurrentlyOnCall']) => (userIsSelected(user) ? <Icon name="check" /> : null),
        key: 'Checked',
      },
    ];

    const UserResultsSection: FC<{ header: string; users: Array<ApiSchemas['UserIsCurrentlyOnCall']> }> = ({
      header,
      users,
    }) =>
      users.length > 0 && (
        <>
          <Text type="secondary" className={cx('user-results-section-header')}>
            {header}
          </Text>
          <GTable<ApiSchemas['UserIsCurrentlyOnCall']>
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
                    className={cx('info-alert')}
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
              <Alert
                className={cx('info-alert')}
                severity="info"
                title={
                  (
                    <Text type="primary">
                      We display a maximum of 100 users per category. Use the search bar above to refine results. You
                      can search by username, email, or team name.
                    </Text>
                  ) as any
                }
              />
              <UserResultsSection header="On-call now" users={onCallUserSearchResults} />
              <div style={{ marginTop: '10px' }}>
                <UserResultsSection header="Not on-call" users={notOnCallUserSearchResults} />
              </div>
            </>
          )}
        </div>
      )
    );
  }
);
