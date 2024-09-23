import React from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Alert, Button, Stack, Themeable2, withTheme2 } from '@grafana/ui';
import { LocationHelper } from 'helpers/LocationHelper';
import {
  UserActions,
  generateMissingPermissionMessage,
  isUserActionAllowed,
} from 'helpers/authorization/authorization';
import { PAGE, PLUGIN_ROOT, StackSize } from 'helpers/consts';
import { PropsWithRouter, withRouter } from 'helpers/hoc';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';
import { LegacyNavHeading } from 'navbar/LegacyNavHeading';
import { Colors } from 'styles/utils.styles';

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
import { RemoteFilters } from 'containers/RemoteFilters/RemoteFilters';
import { UserSettings } from 'containers/UserSettings/UserSettings';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { UserHelper } from 'models/user/user.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { AppFeature } from 'state/features';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import { getUsersStyles } from './Users.styles';

const DEBOUNCE_MS = 1000;

interface RouteProps {
  id: string;
}

interface UsersProps extends WithStoreProps, PageProps, Themeable2, PropsWithRouter<RouteProps> {}

const REQUIRED_PERMISSION_TO_VIEW_USERS = UserActions.UserSettingsWrite;

interface UsersState extends PageBaseState {
  isWrongTeam: boolean;
  userPkToEdit?: ApiSchemas['User']['pk'] | 'new';

  filters: { search: ''; type: undefined; used: undefined; mine: undefined };
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
      filters: { search: '', type: undefined, used: undefined, mine: undefined },

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
    const { filters } = this.state;
    const { userStore, filtersStore } = store;
    const page = filtersStore.currentTablePageNum[PAGE.Users];

    if (!isUserActionAllowed(REQUIRED_PERMISSION_TO_VIEW_USERS)) {
      return;
    }

    LocationHelper.update({ p: page }, 'partial');
    await userStore.fetchItems(filters, page, invalidateFn);

    this.forceUpdate();
  }, DEBOUNCE_MS);

  componentDidUpdate(prevProps: UsersProps) {
    if (prevProps.router.params.id !== this.props.router.params.id) {
      this.parseParams();
    }
  }

  parseParams = async () => {
    this.setState({ errorData: initErrorDataState() }); // reset wrong team error to false on query parse

    const {
      store,
      router: {
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
      router: {
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
    } = this.props;

    const { userPkToEdit } = this.state;

    const page = filtersStore.currentTablePageNum[PAGE.Users];

    const { count, results, page_size } = UserHelper.getSearchResult(userStore);
    const columns = this.getTableColumns();

    return (
      <>
        {authorizedToViewUsers ? (
          <>
            {this.renderFilters()}
            <GTable
              data-testid="users-table"
              emptyText={results ? 'No users found' : 'Loading...'}
              rowKey="pk"
              data={results}
              columns={columns}
              rowClassName={this.getUserRowClassNameFn(userPkToEdit, userStore.currentUserPk)}
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

  renderFilters() {
    const { query, store, theme } = this.props;
    const styles = getUsersStyles(theme);

    return (
      <div className={styles.filters}>
        <RemoteFilters
          query={query}
          page={PAGE.Users}
          grafanaTeamStore={store.grafanaTeamStore}
          onChange={this.handleFiltersChange}
        />
      </div>
    );
  }

  getUserRowClassNameFn = (userPkToEdit?: ApiSchemas['User']['pk'], currentUserPk?: ApiSchemas['User']['pk']) => {
    const styles = getStyles(this.props.theme);

    return (user: ApiSchemas['User']) => {
      if (user.pk === currentUserPk || user.pk === userPkToEdit) {
        return styles.highlightedRow;
      }

      return '';
    };
  };

  handleFiltersChange = (filters: UsersState['filters'], _isOnMount: boolean) => {
    const { filtersStore } = this.props.store;
    const currentTablePage = filtersStore.currentTablePageNum[PAGE.Users];

    LocationHelper.update({ p: currentTablePage }, 'partial');

    this.setState({ filters }, () => {
      this.updateUsers();
    });
  };

  renderTitle = (user: ApiSchemas['User']) => {
    const {
      store: { userStore },
      theme,
    } = this.props;
    const isCurrent = userStore.currentUserPk === user.pk;
    const styles = getUsersStyles(theme);

    return (
      <Stack>
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
      </Stack>
    );
  };

  renderNotificationsChain = (user: ApiSchemas['User']) => {
    return user.notification_chain_verbal.default;
  };

  renderImportantNotificationsChain = (user: ApiSchemas['User']) => {
    return user.notification_chain_verbal.important;
  };

  renderButtons = (user: ApiSchemas['User']) => {
    const { store } = this.props;
    const { userStore } = store;

    const isCurrent = userStore.currentUserPk === user.pk;
    const action = isCurrent ? UserActions.UserSettingsWrite : UserActions.UserSettingsAdmin;

    return (
      <Stack direction="column" justifyContent="center">
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
      </Stack>
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
      warnings.push('No default notification rules');
    }

    if (!this.renderImportantNotificationsChain(user)) {
      warnings.push('No important notification rules');
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
        <Stack>
          <TooltipBadge
            borderType="warning"
            icon="exclamation-triangle"
            text={warnings.length}
            tooltipTitle="Warnings"
            tooltipContent={
              <Stack direction="column" gap={StackSize.none}>
                {warnings.map((warning, index) => (
                  <Text type="primary" key={index}>
                    {warning}
                  </Text>
                ))}
              </Stack>
            }
          />
        </Stack>
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
        title: 'Default notification rules',
        key: 'notifications-chain',
        render: this.renderNotificationsChain,
      },
      {
        width: '20%',
        title: 'Important notification rules',
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

  handleHideUserSettings = () => {
    const {
      router: { navigate },
    } = this.props;
    this.setState({ userPkToEdit: undefined });

    navigate(`${PLUGIN_ROOT}/users`);
  };
}

const getStyles = (theme: GrafanaTheme2) => {
  return {
    highlightedRow: css`
      background: ${theme.isLight ? Colors.GRAY_9 : Colors.CYAN_1};
    `,
  };
};

export const UsersPage = withRouter<RouteProps, Omit<UsersProps, 'store' | 'meta' | 'theme'>>(
  withMobXProviderContext(withTheme2(Users))
);
