import React from 'react';

import { AppRootProps } from '@grafana/data';
import { getLocationSrv } from '@grafana/runtime';
import { Alert, Button, HorizontalGroup, Icon, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';

import Avatar from 'components/Avatar/Avatar';
import GTable from 'components/GTable/GTable';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import UsersFilters from 'components/UsersFilters/UsersFilters';
import UserSettings from 'containers/UserSettings/UserSettings';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { CrossCircleIcon } from 'icons';
import { getRole } from 'models/user/user.helpers';
import { User, User as UserType, UserRole } from 'models/user/user.types';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';

import { getRealFilters, getUserRowClassNameFn } from './Users.helpers';

import styles from './Users.module.css';

const cx = cn.bind(styles);

interface UsersProps extends WithStoreProps, AppRootProps {}

const ITEMS_PER_PAGE = 100;

interface UsersState {
  page: number;
  userPkToEdit?: UserType['pk'] | 'new';
  usersFilters?: {
    searchTerm: string;
    roles?: UserRole[];
  };
}

@observer
class Users extends React.Component<UsersProps, UsersState> {
  state: UsersState = {
    page: 1,
    userPkToEdit: undefined,
    usersFilters: {
      searchTerm: '',
      roles: [UserRole.ADMIN, UserRole.EDITOR, UserRole.VIEWER],
    },
  };

  initialUsersLoaded = false;

  async componentDidMount() {
    const {
      store,
      query: { p },
    } = this.props;

    this.setState({ page: p ? Number(p) : 1 }, this.updateUsers);

    this.parseParams();
  }

  updateUsers = async () => {
    const { store } = this.props;
    const { usersFilters, page } = this.state;
    const { userStore } = store;

    if (!store.isUserActionAllowed(UserAction.ViewOtherUsers)) {
      return;
    }

    getLocationSrv().update({ query: { p: page }, partial: true });
    return await userStore.updateItems(getRealFilters(usersFilters), page);
  };

  componentDidUpdate(prevProps: Readonly<UsersProps>, prevState: Readonly<UsersState>, snapshot?: any) {
    const { store } = this.props;

    if (!this.initialUsersLoaded && store.isUserActionAllowed(UserAction.ViewOtherUsers)) {
      this.updateUsers();
      this.initialUsersLoaded = true;
    }

    if (this.props.query.id !== prevProps.query.id) {
      this.parseParams();
    }
  }

  parseParams = async () => {
    const {
      store,
      query: { id },
    } = this.props;

    if (id) {
      await (id === 'me' ? store.userStore.loadCurrentUser() : store.userStore.loadUser(String(id)));

      const userPkToEdit = String(id === 'me' ? store.userStore.currentUserPk : id);

      if (store.userStore.items[userPkToEdit]) {
        this.setState({ userPkToEdit });
      }
    }
  };

  render() {
    const { usersFilters, userPkToEdit, page } = this.state;
    const { store } = this.props;
    const { userStore } = store;

    const columns = [
      {
        width: '25%',
        key: 'username',
        title: 'User',
        render: this.renderTitle,
      },
      {
        width: '5%',
        title: 'Role',
        key: 'role',
        render: this.renderRole,
      },
      {
        width: '20%',
        title: 'Status',
        key: 'note',
        render: this.renderNote,
      },
      // {
      //   width: '15%',
      //   key: 'contacts',
      //   render: this.renderContacts,
      // },
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
    const handleClear = () =>
      this.setState(
        { usersFilters: { searchTerm: '', roles: [UserRole.ADMIN, UserRole.EDITOR, UserRole.VIEWER] } },
        () => {
          this.debouncedUpdateUsers();
        }
      );

    const { count, results } = userStore.getSearchResult();

    return (
      <div className={cx('root')}>
        <div className={cx('root', 'TEST-users-page')}>
          <div className={cx('users-header')}>
            <div style={{ display: 'flex', alignItems: 'baseline' }}>
              <div>
                <Text.Title level={3}>Users</Text.Title>
                <Text type="secondary">
                  To manage permissions or add users, please visit <a href="/org/users">Grafana user management</a>
                </Text>
              </div>
            </div>
            <PluginLink partial query={{ id: 'me' }}>
              <Button variant="primary" icon="user">
                View my profile
              </Button>
            </PluginLink>
          </div>
          {store.isUserActionAllowed(UserAction.ViewOtherUsers) ? (
            <>
              <div className={cx('user-filters-container')}>
                <UsersFilters
                  className={cx('users-filters')}
                  value={usersFilters}
                  onChange={this.handleUsersFiltersChange}
                />
                <Button variant="secondary" icon="times" onClick={handleClear} className={cx('searchIntegrationClear')}>
                  Clear filters
                </Button>
              </div>

              <GTable
                emptyText={results ? 'No users found' : 'Loading...'}
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
              /* @ts-ignore */
              title={
                <>
                  You don't have enough permissions to view other users because you are not Admin.{' '}
                  <PluginLink query={{ page: 'users', id: 'me' }}>Click here</PluginLink> to open your profile
                </>
              }
              severity="info"
            />
          )}
        </div>
        {userPkToEdit && <UserSettings id={userPkToEdit} onHide={this.handleHideUserSettings} />}
      </div>
    );
  }

  handleChangePage = (page: number) => {
    this.setState({ page }, this.updateUsers);
  };

  renderTitle = (user: UserType) => {
    return (
      <HorizontalGroup>
        <Avatar className={cx('user-avatar')} size="large" src={user.avatar} />
        <div>
          <div>{user.username}</div>
          <Text type="secondary">{user.email}</Text>
          <br />
          <Text type="secondary">{user.verified_phone_number}</Text>
        </div>
      </HorizontalGroup>
    );
  };

  renderRole = (user: UserType) => {
    return getRole(user.role);
  };

  renderNotificationsChain = (user: UserType) => {
    return user.notification_chain_verbal.default;
  };

  renderImportantNotificationsChain = (user: UserType) => {
    return user.notification_chain_verbal.important;
  };

  renderContacts = (user: UserType) => {
    return (
      <div className={cx('contacts')}>
        <div className={cx('contact')}>Slack: {user.slack_user_identity?.name || '-'}</div>
        <div className={cx('contact')}>Telegram: {user.telegram_configuration?.telegram_nick_name || '-'}</div>
      </div>
    );
  };

  renderButtons = (user: UserType) => {
    const { store } = this.props;
    const { userStore } = store;

    const isCurrent = userStore.currentUserPk === user.pk;
    const action = isCurrent ? UserAction.UpdateOwnSettings : UserAction.UpdateOtherUsersSettings;

    return (
      <VerticalGroup justify="center">
        <PluginLink partial query={{ id: user.pk }} disabled={!store.isUserActionAllowed(action)}>
          <WithPermissionControl userAction={action}>
            <Button
              className={cx({
                'TEST-edit-my-own-settings-button': isCurrent,
              })}
              fill="text"
            >
              Edit
            </Button>
          </WithPermissionControl>
        </PluginLink>
      </VerticalGroup>
    );
  };

  renderNote = (user: UserType) => {
    const { store } = this.props;
    if (store.hasFeature(AppFeature.CloudNotifications)) {
      switch (user.cloud_connection_status) {
        case 0:
          return (
            <div className={cx('error-icon')}>
              <CrossCircleIcon /> Cloud is not synced
            </div>
          );

        case 1:
          return (
            <div className={cx('error-icon')}>
              <CrossCircleIcon /> User not matched with cloud
            </div>
          );

        case 2:
          return (
            <>
              <Icon className={cx('warning-message')} name="exclamation-triangle" />{' '}
              <Text type="warning">Phone number is not verified in Grafana Cloud</Text>
            </>
          );
        case 3:
          return (
            <>
              <Icon className={cx('success-message')} name="check-circle" />{' '}
              <Text type="success">Phone number verified</Text>
            </>
          );
      }
    } else {
      if (!user.verified_phone_number || !user.slack_user_identity) {
        let texts = [];

        if (!user.verified_phone_number) {
          texts.push('Phone not verified');
        }
        if (!user.slack_user_identity) {
          texts.push('Slack not verified');
        }
        if (!user.telegram_configuration) {
          texts.push('Telegram not verified');
        }

        return (
          <div>
            <Icon className={cx('warning-message-icon')} name="exclamation-triangle" />
            {texts.join(', ')}
          </div>
        );
      }
    }

    return 'All contacts verified';
  };

  debouncedUpdateUsers = debounce(this.updateUsers, 500);

  handleUsersFiltersChange = (usersFilters: any) => {
    this.setState({ usersFilters, page: 1 }, () => {
      this.debouncedUpdateUsers();
    });
  };

  handleHideUserSettings = () => {
    this.setState({ userPkToEdit: undefined });

    getLocationSrv().update({ partial: true, query: { id: undefined } });
  };

  handleUserUpdate = () => {
    this.updateUsers();
  };
}

export default withMobXProviderContext(Users);
