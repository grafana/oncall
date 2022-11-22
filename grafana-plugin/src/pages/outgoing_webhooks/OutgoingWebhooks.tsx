import React from 'react';

import { getLocationSrv } from '@grafana/runtime';
import { Button, HorizontalGroup } from '@grafana/ui';
import { PluginPage } from 'PluginPage';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import LegacyNavHeading from 'navbar/LegacyNavHeading';
import { AppRootProps } from 'types';

import GTable from 'components/GTable/GTable';
import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import {
  getWrongTeamResponseInfo,
  initErrorDataState,
} from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import OutgoingWebhookForm from 'containers/OutgoingWebhookForm/OutgoingWebhookForm';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { ActionDTO } from 'models/action';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { pages } from 'pages';
import { getQueryParams } from 'plugin/GrafanaPluginRootPage.helpers';
import { WithStoreProps } from 'state/types';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';

import styles from './OutgoingWebhooks.module.css';

const cx = cn.bind(styles);

interface OutgoingWebhooksProps extends WithStoreProps, AppRootProps {}

interface OutgoingWebhooksState extends PageBaseState {
  outgoingWebhookIdToEdit?: OutgoingWebhook['id'] | 'new';
}

@observer
class OutgoingWebhooks extends React.Component<OutgoingWebhooksProps, OutgoingWebhooksState> {
  state: OutgoingWebhooksState = {
    errorData: initErrorDataState(),
  };

  private outgoingWebhookId: string;

  async componentDidMount() {
    this.update().then(this.parseQueryParams);
  }

  componentDidUpdate() {
    if (this.outgoingWebhookId !== getQueryParams()['id']) {
      this.parseQueryParams();
    }
  }

  parseQueryParams = async () => {
    this.setState((_prevState) => ({
      errorData: initErrorDataState(),
      outgoingWebhookIdToEdit: undefined,
    })); // reset state on query parse

    const { store } = this.props;
    const { id } = getQueryParams();

    this.outgoingWebhookId = id;

    if (!id) {
      return;
    }

    let outgoingWebhook: OutgoingWebhook | void = undefined;
    const isNewWebhook = id === 'new';

    if (!isNewWebhook) {
      outgoingWebhook = await store.outgoingWebhookStore
        .loadItem(id, true)
        .catch((error) => this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } }));
    }

    if (outgoingWebhook || isNewWebhook) {
      this.setState({ outgoingWebhookIdToEdit: id });
    }
  };

  update = () => {
    const { store } = this.props;

    return store.outgoingWebhookStore.updateItems();
  };

  render() {
    const { store, query } = this.props;
    const { outgoingWebhookIdToEdit, errorData } = this.state;

    const webhooks = store.outgoingWebhookStore.getSearchResult();

    const columns = [
      {
        width: '40%',
        title: 'Name',
        dataIndex: 'name',
      },
      {
        width: '40%',
        title: 'Url',
        dataIndex: 'webhook',
      },
      {
        width: '20%',
        key: 'action',
        render: this.renderActionButtons,
      },
    ];

    return (
      <PluginPage pageNav={pages['outgoing_webhooks'].getPageNav()}>
        <PageErrorHandlingWrapper
          errorData={errorData}
          objectName="outgoing webhook"
          pageName="outgoing_webhooks"
          itemNotFoundMessage={`Outgoing webhook with id=${query?.id} is not found. Please select outgoing webhook from the list.`}
        >
          <>
            <div className={cx('root')}>
              <GTable
                emptyText={webhooks ? 'No outgoing webhooks found' : 'Loading...'}
                title={() => (
                  <div className={cx('header')}>
                    <LegacyNavHeading>
                      <Text.Title level={3}>Outgoing Webhooks</Text.Title>
                    </LegacyNavHeading>
                    <div className="u-pull-right">
                      <PluginLink
                        partial
                        query={{ id: 'new' }}
                        disabled={!store.isUserActionAllowed(UserAction.UpdateCustomActions)}
                      >
                        <WithPermissionControl userAction={UserAction.UpdateCustomActions}>
                          <Button variant="primary" icon="plus">
                            Create
                          </Button>
                        </WithPermissionControl>
                      </PluginLink>
                    </div>
                  </div>
                )}
                rowKey="id"
                columns={columns}
                data={webhooks}
              />
            </div>
            {outgoingWebhookIdToEdit && (
              <OutgoingWebhookForm
                id={outgoingWebhookIdToEdit}
                onUpdate={this.update}
                onHide={this.handleOutgoingWebhookFormHide}
              />
            )}
          </>
        </PageErrorHandlingWrapper>
      </PluginPage>
    );
  }

  renderActionButtons = (record: ActionDTO) => {
    return (
      <HorizontalGroup justify="flex-end">
        <WithPermissionControl key={'edit_action'} userAction={UserAction.UpdateCustomActions}>
          <Button onClick={this.getEditClickHandler(record.id)} fill="text">
            Edit
          </Button>
        </WithPermissionControl>
        <WithPermissionControl key={'delete_action'} userAction={UserAction.UpdateCustomActions}>
          <WithConfirm>
            <Button onClick={this.getDeleteClickHandler(record.id)} fill="text" variant="destructive">
              Delete
            </Button>
          </WithConfirm>
        </WithPermissionControl>
      </HorizontalGroup>
    );
  };

  getDeleteClickHandler = (id: OutgoingWebhook['id']) => {
    const { store } = this.props;
    return () => {
      store.alertReceiveChannelStore.deleteCustomButton(id).then(this.update);
    };
  };

  getEditClickHandler = (id: OutgoingWebhook['id']) => {
    return () => {
      this.setState({ outgoingWebhookIdToEdit: id });

      getLocationSrv().update({ partial: true, query: { id } });
    };
  };

  handleOutgoingWebhookFormHide = () => {
    this.setState({ outgoingWebhookIdToEdit: undefined });

    getLocationSrv().update({ partial: true, query: { id: undefined } });
  };
}

export { OutgoingWebhooks };

export default withMobXProviderContext(OutgoingWebhooks);
