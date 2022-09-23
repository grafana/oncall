import React from 'react';

import { Button, HorizontalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import moment from 'moment';

import GTable from 'components/GTable/GTable';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { ApiToken } from 'models/api_token/api_token.types';
import { WithStoreProps } from 'state/types';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';

import ApiTokenForm from './ApiTokenForm';

import styles from './ApiTokenSettings.module.css';

const cx = cn.bind(styles);

const MAX_TOKENS_PER_USER = 5;

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

    return (
      <>
        <GTable
          title={() => (
            <div className={cx('header')}>
              <HorizontalGroup align="flex-end">
                <Text.Title level={3}>API Tokens</Text.Title>
                {/*<a target="_blank" href="https://a-03-dev-us-central-0.grafana.net/api-docs/#introduction">
                  API Docs
                </a>
                <Text type="secondary">|</Text>
                <a target="_blank" href="https://github.com/grafana/amixr/tree/dev/docs/terraform-provider">
                  Terraform Docs
                </a>*/}
              </HorizontalGroup>
              <WithPermissionControl userAction={UserAction.UpdateApiTokens}>
                <Button
                  icon="plus"
                  disabled={apiTokens && apiTokens.length >= MAX_TOKENS_PER_USER}
                  onClick={() => {
                    this.setState({ showCreateTokenModal: true });
                  }}
                >
                  Create
                </Button>
              </WithPermissionControl>
            </div>
          )}
          rowKey="id"
          className="api-keys"
          showHeader={!isMobile}
          data={apiTokens}
          emptyText={
            store.isUserActionAllowed(UserAction.UpdateApiTokens)
              ? apiTokens
                ? 'No tokens found'
                : 'Loading...'
              : 'API tokens are available only for users with Admin permissions'
          }
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
      <WithPermissionControl userAction={UserAction.UpdateApiTokens}>
        <WithConfirm title={`Are you sure to revoke "${record.name}" API token?`} confirmText="Revoke token">
          <Button fill="text" variant="destructive" onClick={this.getRevokeTokenClickHandler(record.id)}>
            Revoke
          </Button>
        </WithConfirm>
      </WithPermissionControl>
    );

    return revokeButton;
  };

  renderCreatedAt = (record: ApiToken) => {
    const date = moment(record.created_at);
    return <span> {date.format('MMM DD, YYYY hh:mm A')}</span>;
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
