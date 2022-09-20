import React from 'react';

import { AppRootProps } from '@grafana/data';
import { getLocationSrv } from '@grafana/runtime';
import { Button, HorizontalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import GTable from 'components/GTable/GTable';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import WrongTeamDisplayWrapper, { initWrongTeamDataState, WrongTeamData } from 'components/WrongTeamDisplayWrapper/WrongTeamDisplayWrapper';
import { getWrongTeamResponseInfo } from 'components/WrongTeamDisplayWrapper/WrongTeamDisplayWrapper.helpers';
import OutgoingWebhookForm from 'containers/OutgoingWebhookForm/OutgoingWebhookForm';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { ActionDTO } from 'models/action';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { WithStoreProps } from 'state/types';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';

import styles from './OutgoingWebhooks.module.css';

const cx = cn.bind(styles);

interface OutgoingWebhooksProps extends WithStoreProps, AppRootProps {}

interface OutgoingWebhooksState {
  outgoingWebhookIdToEdit?: OutgoingWebhook['id'] | 'new';
  wrongTeamData: WrongTeamData;
}

@observer
class OutgoingWebhooks extends React.Component<OutgoingWebhooksProps, OutgoingWebhooksState> {
  state: OutgoingWebhooksState = {
    wrongTeamData: initWrongTeamDataState(),
  };

  async componentDidMount() {
    this.update().then(this.parseQueryParams);
  }

  componentDidUpdate(prevProps: OutgoingWebhooksProps) {
    if (this.props.query.id !== prevProps.query.id) {
      this.parseQueryParams();
    }
  }

  parseQueryParams = async () => {
    this.setState((prevState) => ({
      wrongTeamData: initWrongTeamDataState(),
      outgoingWebhookIdToEdit: undefined,
    })); // reset state on query parse

    const {
      store,
      query: { id },
    } = this.props;

    await store.outgoingWebhookStore
      .loadItem(id, true)
      .catch((error) => this.setState({ wrongTeamData: { ...getWrongTeamResponseInfo(error) } }));

    if (id) {
      this.setState({ outgoingWebhookIdToEdit: id });
    }
  };

  update = () => {
    const { store } = this.props;

    return store.outgoingWebhookStore.updateItems();
  };

  render() {
    const { store } = this.props;
    const { outgoingWebhookIdToEdit, wrongTeamData } = this.state;

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
      <WrongTeamDisplayWrapper wrongTeamData={wrongTeamData} objectName="outgoing webhook" pageName="outgoing_webhooks">
        {() => (
          <>
            <div className={cx('root')}>
              <GTable
                emptyText={webhooks ? 'No outgoing webhooks found' : 'Loading...'}
                title={() => (
                  <div className={cx('header')}>
                    <Text.Title level={3}>Outgoing Webhooks</Text.Title>
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
        )}
      </WrongTeamDisplayWrapper>
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

export default withMobXProviderContext(OutgoingWebhooks);
