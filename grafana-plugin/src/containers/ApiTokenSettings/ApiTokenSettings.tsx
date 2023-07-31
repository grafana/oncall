import React from 'react';

import { Button, HorizontalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';

import GTable from 'components/GTable/GTable';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ApiToken } from 'models/api_token/api_token.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { generateMissingPermissionMessage, isUserActionAllowed, UserActions } from 'utils/authorization';

import ApiTokenForm from './ApiTokenForm';

import styles from './ApiTokenSettings.module.css';

const cx = cn.bind(styles);

const MAX_TOKENS_PER_USER = 5;
const REQUIRED_PERMISSION_TO_VIEW = UserActions.APIKeysWrite;

interface ApiTokensProps extends WithStoreProps {}

@observer
class ApiTokens extends React.Component<ApiTokensProps, any> {
  constructor(props: any) {
    super(props);

    this.state = { showCreateTokenModal: false };
  }

  componentDidMount() {
    const {
      store: { apiTokenStore },
    } = this.props;

    apiTokenStore.updateItems();
  }

  render() {
    const { store } = this.props;
    const { apiTokenStore } = store;

    const { isMobile } = store;

    const apiTokens = apiTokenStore.getSearchResult();

    const { showCreateTokenModal } = this.state;

    const columns = [
      {
        title: 'Name',
        dataIndex: 'name',
      },
      {
        title: 'Created At',
        key: 'created_at',
        render: this.renderCreatedAt,
      },
      {
        width: 100,
        key: 'action',
        render: this.renderActionButtons,
      },
    ];

    const authorizedToViewAPIKeys = isUserActionAllowed(REQUIRED_PERMISSION_TO_VIEW);

    let emptyText = 'Loading...';
    if (!authorizedToViewAPIKeys) {
      emptyText = `${generateMissingPermissionMessage(REQUIRED_PERMISSION_TO_VIEW)} to be able to view API tokens.`;
    } else if (apiTokens) {
      emptyText = 'No tokens found';
    }

    return (
      <>
        <GTable
          title={() => (
            <div className={cx('header')}>
              <HorizontalGroup align="flex-end">
                <Text.Title level={3}>API Tokens</Text.Title>
              </HorizontalGroup>
              <WithPermissionControlTooltip userAction={UserActions.APIKeysWrite}>
                <Button
                  icon="plus"
                  disabled={apiTokens && apiTokens.length >= MAX_TOKENS_PER_USER}
                  onClick={() => {
                    this.setState({ showCreateTokenModal: true });
                  }}
                >
                  Create
                </Button>
              </WithPermissionControlTooltip>
            </div>
          )}
          rowKey="id"
          className="api-keys"
          showHeader={!isMobile}
          data={apiTokens}
          emptyText={emptyText}
          columns={columns}
        />
        {showCreateTokenModal && (
          <ApiTokenForm
            visible={showCreateTokenModal}
            onUpdate={this.handleCreateToken}
            onHide={() => {
              this.setState({ showCreateTokenModal: false });
            }}
          />
        )}
      </>
    );
  }

  renderActionButtons = (record: ApiToken) => {
    const revokeButton = (
      <WithPermissionControlTooltip userAction={UserActions.APIKeysWrite}>
        <WithConfirm title={`Are you sure to revoke "${record.name}" API token?`} confirmText="Revoke token">
          <Button fill="text" variant="destructive" onClick={this.getRevokeTokenClickHandler(record.id)}>
            Revoke
          </Button>
        </WithConfirm>
      </WithPermissionControlTooltip>
    );

    return revokeButton;
  };

  renderCreatedAt = (record: ApiToken) => {
    const date = moment(record.created_at);
    return <span> {date.format('MMM DD, YYYY hh:mm')}</span>;
  };

  getRevokeTokenClickHandler = (id: ApiToken['id']) => {
    const {
      store: { apiTokenStore },
    } = this.props;

    return () => {
      apiTokenStore.revokeApiToken(id).then(() => {
        apiTokenStore.updateItems();
      });
    };
  };

  handleCreateToken = () => {
    const {
      store: { apiTokenStore },
    } = this.props;

    apiTokenStore.updateItems();
  };
}

export default withMobXProviderContext(ApiTokens);
