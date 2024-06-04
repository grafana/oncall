import React from 'react';

import { cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Alert, Button, HorizontalGroup, VerticalGroup, withTheme2 } from '@grafana/ui';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';
import { LegacyNavHeading } from 'navbar/LegacyNavHeading';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import { Avatar } from 'components/Avatar/Avatar';
import { GTable } from 'components/GTable/GTable';
import { PageErrorHandlingWrapper, PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import {
  getWrongTeamResponseInfo,
  initErrorDataState,
} from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { TooltipBadge } from 'components/TooltipBadge/TooltipBadge';
import { UsersFilters } from 'components/UsersFilters/UsersFilters';
import { UserSettings } from 'containers/UserSettings/UserSettings';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserHelper } from 'models/user/user.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { AppFeature } from 'state/features';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { LocationHelper } from 'utils/LocationHelper';
import { UserActions, generateMissingPermissionMessage, isUserActionAllowed } from 'utils/authorization/authorization';
import { PAGE, PLUGIN_ROOT } from 'utils/consts';

import { getUserRowClassNameFn } from './Users.helpers';
import { getUsersStyles } from './Users.styles';

const DEBOUNCE_MS = 1000;

interface UsersProps extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {
  theme: GrafanaTheme2;
}

const REQUIRED_PERMISSION_TO_VIEW_USERS = UserActions.UserSettingsWrite;

interface UsersState extends PageBaseState {
  isWrongTeam: boolean;
  userPkToEdit?: ApiSchemas['User']['pk'] | 'new';
  usersFilters?: {
    searchTerm: string;
  };
}

@observer
class Users extends React.Component<UsersProps, UsersState> {
  constructor(props: UsersProps) {
    super(props);

    const {
      query: { p },
      store: { filtersStore },
    } = props;

    this.state = {
      isWrongTeam: false,
      userPkToEdit: undefined,
      usersFilters: {
        searchTerm: '',
      },

      errorData: initErrorDataState(),
    };

    // Users component doesn't rely on RemoteFilters
    // therefore we need to initialize the page in the constructor instead
    filtersStore.currentTablePageNum[PAGE.Users] = p ? Number(p) : 1;
  }

  async componentDidMount() {
    this.parseParams();
  }

  updateUsers = debounce(async (invalidateFn?: () => boolean) => {
    const { store } = this.props;
    const { usersFilters } = this.state;
    const { userStore, filtersStore } = store;
    const page = filtersStore.currentTablePageNum[PAGE.Users];

    if (!isUserActionAllowed(REQUIRED_PERMISSION_TO_VIEW_USERS)) {
      return;
    }

    LocationHelper.update({ p: page }, 'partial');
    await userStore.fetchItems(usersFilters, page, invalidateFn);

    this.forceUpdate();
  }, DEBOUNCE_MS);

  componentDidUpdate(prevProps: UsersProps) {
    if (prevProps.match.params.id !== this.props.match.params.id) {
      this.parseParams();
    }
  }

  parseParams = async () => {
    this.setState({ errorData: initErrorDataState() }); // reset wrong team error to false on query parse

    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;

    if (id) {
      try {
        await (id === 'me'
          ? store.userStore.loadCurrentUser()
          : store.userStore.fetchItemById({ userPk: String(id), skipErrorHandling: true }));
      } catch (error) {
        this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } });
      }

      const userPkToEdit = String(id === 'me' ? store.userStore.currentUserPk : id);

      if (store.userStore.items[userPkToEdit]) {
        this.setState({ userPkToEdit });
      }
    }
  };

  render() {
    const { userPkToEdit, errorData } = this.state;
    const {
      match: {
        params: { id },
      },
      theme,
    } = this.props;

    const isAuthorizedToViewUsers = isUserActionAllowed(REQUIRED_PERMISSION_TO_VIEW_USERS);
    const styles = getUsersStyles(theme);

    return (
      <PageErrorHandlingWrapper
        errorData={errorData}
        objectName="user"
        pageName="users"
        itemNotFoundMessage={`User with id=${id} is not found. Please select user from the list.`}
      >
        {() => (
          <div>
            <div className={styles.usersHeader}>
              <div className={styles.usersHeaderLeft}>
                <div>
                  <LegacyNavHeading>
                    <Text.Title level={3}>Users</Text.Title>
                  </LegacyNavHeading>
                  {isAuthorizedToViewUsers && (
                    <Text type="secondary">
                      All Grafana users listed below to set notification preferences. To manage permissions or add new
                      users, please visit{' '}
                      <a href="/admin/users" target="_blank">
                        Grafana user management
                      </a>
                    </Text>
                  )}
                </div>
              </div>
              <PluginLink query={{ page: 'users', id: 'me' }}>
                <Button variant="primary" icon="user" data-testid="users-view-my-profile">
                  View my profile
                </Button>
              </PluginLink>
            </div>

            {this.renderContentIfAuthorized(isAuthorizedToViewUsers)}

            {userPkToEdit && <UserSettings id={userPkToEdit} onHide={this.handleHideUserSettings} />}
          </div>
        )}
      </PageErrorHandlingWrapper>
    );
  }

  renderContentIfAuthorized(authorizedToViewUsers: boolean) {
    const {
      store: { userStore, filtersStore },
      theme,
    } = this.props;

    const { usersFilters, userPkToEdit } = this.state;

    const page = filtersStore.currentTablePageNum[PAGE.Users];

    const { count, results, page_size } = UserHelper.getSearchResult(userStore);
    const columns = this.getTableColumns();

    const handleClear = () =>
      this.setState({ usersFilters: { searchTerm: '' } }, () => {
        this.updateUsers();
      });
    const styles = getUsersStyles(theme);

    return (
      <>
        {authorizedToViewUsers ? (
          <>
            <div className={styles.userFiltersContainer} data-testid="users-filters">
              <UsersFilters
                className={styles.usersFilters}
                value={usersFilters}
                isLoading={results === undefined}
                onChange={this.handleUsersFiltersChange}
              />
              <Button variant="secondary" icon="times" onClick={handleClear}>
                Clear filters
              </Button>
            </div>

            <GTable
              data-testid="users-table"
              emptyText={results ? 'No users found' : 'Loading...'}
              rowKey="pk"
              data={results}
              columns={columns}
              rowClassName={getUserRowClassNameFn(userPkToEdit, userStore.currentUserPk)}
              pagination={{
                page,
                total: results ? Math.ceil((count || 0) / page_size) : 0,
                onChange: this.handleChangePage,
              }}
            />
          </>
        ) : (
          <Alert
            title={
              (
                <div data-testid="users-missing-permissions">
                  <Text type="primary">
                    {generateMissingPermissionMessage(REQUIRED_PERMISSION_TO_VIEW_USERS)} to be able to view OnCall
                    users. <PluginLink query={{ page: 'users', id: 'me' }}>Click here</PluginLink> to open your profile
                  </Text>
                </div>
              ) as any
            }
            data-testid="view-users-missing-permission-message"
            severity="info"
          />
        )}
      </>
    );
  }

  renderTitle = (user: ApiSchemas['User']) => {
    const {
      store: { userStore },
      theme,
    } = this.props;
    const isCurrent = userStore.currentUserPk === user.pk;
    const styles = getUsersStyles(theme);

    return (
      <HorizontalGroup>
        <Avatar className={styles.userAvatar} size="large" src={user.avatar} />
        <div
          className={cx({
            'current-user': isCurrent,
            'other-user': !isCurrent,
          })}
        >
          <div data-testid="users-username">{user.username}</div>
          <Text type="secondary" data-testid="users-email">
            {user.email}
          </Text>
          <br />
          <Text type="secondary" data-testid="users-phone-number">
            {user.verified_phone_number}
          </Text>
        </div>
      </HorizontalGroup>
    );
  };

  renderNotificationsChain = (user: ApiSchemas['User']) => {
    return user.notification_chain_verbal.default;
  };

  renderImportantNotificationsChain = (user: ApiSchemas['User']) => {
    return user.notification_chain_verbal.important;
  };

  renderContacts = (user: ApiSchemas['User']) => {
    const { store } = this.props;
    return (
      <div>
        <div>Slack: {user.slack_user_identity?.name || '-'}</div>
        {store.hasFeature(AppFeature.Telegram) && (
          <div>Telegram: {user.telegram_configuration?.telegram_nick_name || '-'}</div>
        )}
      </div>
    );
  };

  renderButtons = (user: ApiSchemas['User']) => {
    const { store } = this.props;
    const { userStore } = store;

    const isCurrent = userStore.currentUserPk === user.pk;
    const action = isCurrent ? UserActions.UserSettingsWrite : UserActions.UserSettingsAdmin;

    return (
      <VerticalGroup justify="center">
        <PluginLink query={{ page: 'users', id: user.pk }} disabled={!isUserActionAllowed(action)}>
          <WithPermissionControlTooltip userAction={action}>
            <Button
              className={cx({
                'edit-my-profile-button': isCurrent,
                'edit-other-profile-button': !isCurrent,
              })}
              fill="text"
            >
              Edit
            </Button>
          </WithPermissionControlTooltip>
        </PluginLink>
      </VerticalGroup>
    );
  };

  renderStatus = (user: ApiSchemas['User']) => {
    const {
      store,
      store: { organizationStore, telegramChannelStore },
    } = this.props;

    if (user.hidden_fields === true) {
      return null;
    }

    let warnings = [];

    // Show warnining if no notifications are set
    if (!this.renderNotificationsChain(user)) {
      warnings.push('No Default Notifications');
    }

    if (!this.renderImportantNotificationsChain(user)) {
      warnings.push('No Important Notifications');
    }

    let phone_verified = user.verified_phone_number !== null;
    if (user.cloud_connection_status !== null) {
      phone_verified = false;
      switch (user.cloud_connection_status) {
        case 0:
          break; // Cloud is not connected, no need to show warning to the user
        case 1:
          warnings.push('User not matched with cloud');
          break;
        case 2:
          warnings.push('Phone number is not verified in Grafana Cloud OnCall');
          break;
        case 3:
          phone_verified = true; // Phone is verified in Grafana Cloud OnCall, no need to show warning to the user
          break;
      }
    } else if (!phone_verified) {
      warnings.push('Phone not verified');
    }

    if (organizationStore.currentOrganization?.slack_team_identity && !user.slack_user_identity) {
      warnings.push('Slack profile is not connected');
    }

    let telegramChannelsExist = telegramChannelStore.currentTeamToTelegramChannel?.length > 0;

    if (store.hasFeature(AppFeature.Telegram) && telegramChannelsExist && !user.telegram_configuration) {
      warnings.push('Telegram profile is not connected');
    }

    return (
      warnings.length > 0 && (
        <HorizontalGroup>
          <TooltipBadge
            borderType="warning"
            icon="exclamation-triangle"
            text={warnings.length}
            tooltipTitle="Warnings"
            tooltipContent={
              <VerticalGroup spacing="none">
                {warnings.map((warning, index) => (
                  <Text type="primary" key={index}>
                    {warning}
                  </Text>
                ))}
              </VerticalGroup>
            }
          />
        </HorizontalGroup>
      )
    );
  };

  getTableColumns(): Array<{ width: string; key: string; title?: string; render }> {
    return [
      {
        width: '25%',
        key: 'username',
        title: 'User',
        render: this.renderTitle,
      },
      {
        width: '20%',
        title: 'Status',
        key: 'note',
        render: this.renderStatus,
      },
      {
        width: '20%',
        title: 'Default Notifications',
        key: 'notifications-chain',
        render: this.renderNotificationsChain,
      },
      {
        width: '20%',
        title: 'Important Notifications',
        key: 'important-notifications-chain',
        render: this.renderImportantNotificationsChain,
      },
      {
        width: '5%',
        key: 'buttons',
        render: this.renderButtons,
      },
    ];
  }

  handleChangePage = (page: number) => {
    const { filtersStore } = this.props.store;

    filtersStore.currentTablePageNum[PAGE.Users] = page;

    this.updateUsers();
  };

  handleUsersFiltersChange = (usersFilters: any, invalidateFn: () => boolean) => {
    const { filtersStore } = this.props.store;

    filtersStore.currentTablePageNum[PAGE.Users] = 1;

    this.setState({ usersFilters }, () => {
      this.updateUsers(invalidateFn);
    });
  };

  handleHideUserSettings = () => {
    const { history } = this.props;
    this.setState({ userPkToEdit: undefined });

    history.push(`${PLUGIN_ROOT}/users`);
  };
}

export const UsersPage = withRouter(withMobXProviderContext(withTheme2(Users)));
