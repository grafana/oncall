import React from 'react';

import { Alert, Button, HorizontalGroup, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';
import LegacyNavHeading from 'navbar/LegacyNavHeading';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import Avatar from 'components/Avatar/Avatar';
import GTable from 'components/GTable/GTable';
import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import {
  getWrongTeamResponseInfo,
  initErrorDataState,
} from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import TooltipBadge from 'components/TooltipBadge/TooltipBadge';
import UsersFilters from 'components/UsersFilters/UsersFilters';
import UserSettings from 'containers/UserSettings/UserSettings';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { User as UserType } from 'models/user/user.types';
import { AppFeature } from 'state/features';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import LocationHelper from 'utils/LocationHelper';
import { generateMissingPermissionMessage, isUserActionAllowed, UserActions } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';

import { getUserRowClassNameFn } from './Users.helpers';

import styles from './Users.module.css';

const cx = cn.bind(styles);

interface UsersProps extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {}

const ITEMS_PER_PAGE = 100;
const REQUIRED_PERMISSION_TO_VIEW_USERS = UserActions.UserSettingsWrite;

interface UsersState extends PageBaseState {
  page: number;
  isWrongTeam: boolean;
  userPkToEdit?: UserType['pk'] | 'new';
  usersFilters?: {
    searchTerm: string;
  };
  initialUsersLoaded: boolean;
  queuedUpdateUsers: boolean;
}

@observer
class Users extends React.Component<UsersProps, UsersState> {
  constructor(props: UsersProps) {
    super(props);

    const {
      query: { p },
    } = props;

    this.state = {
      page: p ? Number(p) : 1,
      isWrongTeam: false,
      userPkToEdit: undefined,
      usersFilters: {
        searchTerm: '',
      },

      errorData: initErrorDataState(),
      initialUsersLoaded: false,
      queuedUpdateUsers: false,
    };
  }

  async componentDidMount() {
    this.updateUsers();
    this.parseParams();
  }

  updateUsers = async () => {
    const { store } = this.props;
    const { usersFilters, page } = this.state;
    const { userStore } = store;

    if (!isUserActionAllowed(REQUIRED_PERMISSION_TO_VIEW_USERS)) {
      return;
    }

    LocationHelper.update({ p: page }, 'partial');
    await userStore.updateItems(usersFilters, page);

    const { queuedUpdateUsers } = this.state;
    this.setState({ initialUsersLoaded: true, queuedUpdateUsers: false }, () => {
      if (queuedUpdateUsers) {
        this.updateUsers();
      }
    });
  };

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
      await (id === 'me' ? store.userStore.loadCurrentUser() : store.userStore.loadUser(String(id), true)).catch(
        (error) => this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } })
      );

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
    } = this.props;

    const isAuthorizedToViewUsers = isUserActionAllowed(REQUIRED_PERMISSION_TO_VIEW_USERS);

    return (
      <PageErrorHandlingWrapper
        errorData={errorData}
        objectName="user"
        pageName="users"
        itemNotFoundMessage={`User with id=${id} is not found. Please select user from the list.`}
      >
        {() => (
          <div className={cx('root')}>
            <div className={cx('users-header')}>
              <div style={{ display: 'flex', alignItems: 'baseline' }}>
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
      store: { userStore },
    } = this.props;

    const { usersFilters, page, initialUsersLoaded, userPkToEdit, queuedUpdateUsers } = this.state;

    const { count, results } = userStore.getSearchResult();
    const columns = this.getTableColumns();

    const handleClear = () =>
      this.setState({ usersFilters: { searchTerm: '' } }, () => {
        this.updateUsers();
      });

    return (
      <>
        {authorizedToViewUsers ? (
          <>
            <div className={cx('user-filters-container')} data-testid="users-filters">
              <UsersFilters
                className={cx('users-filters')}
                value={usersFilters}
                isLoading={queuedUpdateUsers}
                onChange={this.handleUsersFiltersChange}
              />
              <Button variant="secondary" icon="times" onClick={handleClear} className={cx('searchIntegrationClear')}>
                Clear filters
              </Button>
            </div>

            <GTable
              data-testid="users-table"
              emptyText={initialUsersLoaded ? 'No users found' : 'Loading...'}
              rowKey="pk"
              data={results}
              columns={columns}
              rowClassName={getUserRowClassNameFn(userPkToEdit, userStore.currentUserPk)}
              pagination={{
                page,
                total: Math.ceil((count || 0) / ITEMS_PER_PAGE),
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

  renderTitle = (user: UserType) => {
    const {
      store: { userStore },
    } = this.props;
    const isCurrent = userStore.currentUserPk === user.pk;

    return (
      <HorizontalGroup>
        <Avatar className={cx('user-avatar')} size="large" src={user.avatar} />
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

  renderNotificationsChain = (user: UserType) => {
    return user.notification_chain_verbal.default;
  };

  renderImportantNotificationsChain = (user: UserType) => {
    return user.notification_chain_verbal.important;
  };

  renderContacts = (user: UserType) => {
    const { store } = this.props;
    return (
      <div className={cx('contacts')}>
        <div className={cx('contact')}>Slack: {user.slack_user_identity?.name || '-'}</div>
        {store.hasFeature(AppFeature.Telegram) && (
          <div className={cx('contact')}>Telegram: {user.telegram_configuration?.telegram_nick_name || '-'}</div>
        )}
      </div>
    );
  };

  renderButtons = (user: UserType) => {
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

  renderStatus = (user: UserType) => {
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
          warnings.push('Phone number is not verified in Grafana Cloud');
          break;
        case 3:
          phone_verified = true; // Phone is verified in Grafana Cloud, no need to show warning to the user
          break;
      }
    } else if (!phone_verified) {
      warnings.push('Phone not verified');
    }

    if (organizationStore.currentOrganization.slack_team_identity && !user.slack_user_identity) {
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
    this.setState({ page }, this.updateUsers);
  };

  debouncedUpdateUsers = debounce(this.updateUsers, 500);

  handleUsersFiltersChange = (usersFilters: any) => {
    this.setState({ usersFilters, page: 1 }, () => {
      if (!this.state.initialUsersLoaded) {
        // queue delayed users update
        return this.setState({ queuedUpdateUsers: true });
      }

      this.debouncedUpdateUsers();
    });
  };

  handleHideUserSettings = () => {
    const { history } = this.props;
    this.setState({ userPkToEdit: undefined });

    history.push(`${PLUGIN_ROOT}/users`);
  };
}

export default withRouter(withMobXProviderContext(Users));
