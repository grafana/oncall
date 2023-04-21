import React from 'react';

import { Button, HorizontalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import LegacyNavHeading from 'navbar/LegacyNavHeading';
import { RouteComponentProps, withRouter } from 'react-router-dom';

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
import RemoteFilters from 'containers/RemoteFilters/RemoteFilters';
import TeamName from 'containers/TeamName/TeamName';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ActionDTO } from 'models/action';
import { FiltersValues } from 'models/filters/filters.types';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { isUserActionAllowed, UserActions } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';

import styles from './OutgoingWebhooks.module.css';

const cx = cn.bind(styles);

interface OutgoingWebhooksProps extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {}

interface OutgoingWebhooksState extends PageBaseState {
  outgoingWebhookIdToEdit?: OutgoingWebhook['id'] | 'new';
}

@observer
class OutgoingWebhooks extends React.Component<OutgoingWebhooksProps, OutgoingWebhooksState> {
  state: OutgoingWebhooksState = {
    errorData: initErrorDataState(),
  };

  componentDidUpdate(prevProps: OutgoingWebhooksProps) {
    if (prevProps.match.params.id !== this.props.match.params.id) {
      this.parseQueryParams();
    }
  }

  parseQueryParams = async () => {
    this.setState((_prevState) => ({
      errorData: initErrorDataState(),
      outgoingWebhookIdToEdit: undefined,
    })); // reset state on query parse

    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;

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
        width: '35%',
        title: 'Name',
        dataIndex: 'name',
      },
      {
        width: '35%',
        title: 'Url',
        dataIndex: 'webhook',
      },
      {
        width: '15%',
        title: 'Team',
        render: (item: OutgoingWebhook) => this.renderTeam(item, store.grafanaTeamStore.items),
      },
      {
        width: '15%',
        key: 'action',
        render: this.renderActionButtons,
      },
    ];

    return (
      <PageErrorHandlingWrapper
        errorData={errorData}
        objectName="outgoing webhook"
        pageName="outgoing_webhooks"
        itemNotFoundMessage={`Outgoing webhook with id=${query?.id} is not found. Please select outgoing webhook from the list.`}
      >
        {() => (
          <>
            <div className={cx('root')}>
              {this.renderOutgoingWebhooksFilters()}
              <GTable
                emptyText={webhooks ? 'No outgoing webhooks found' : 'Loading...'}
                title={() => (
                  <div className={cx('header')}>
                    <LegacyNavHeading>
                      <Text.Title level={3}>Outgoing Webhooks</Text.Title>
                    </LegacyNavHeading>
                    <div className="u-pull-right">
                      <PluginLink
                        query={{ page: 'outgoing_webhooks', id: 'new' }}
                        disabled={!isUserActionAllowed(UserActions.OutgoingWebhooksWrite)}
                      >
                        <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                          <Button variant="primary" icon="plus">
                            New outgoing webhook
                          </Button>
                        </WithPermissionControlTooltip>
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
        )}
      </PageErrorHandlingWrapper>
    );
  }

  renderOutgoingWebhooksFilters() {
    const { query, store } = this.props;
    return (
      <div className={cx('filters')}>
        <RemoteFilters
          query={query}
          page="outgoing_webhooks"
          grafanaTeamStore={store.grafanaTeamStore}
          onChange={this.handleFiltersChange}
        />
      </div>
    );
  }

  handleFiltersChange = (filters: FiltersValues, isOnMount) => {
    const { store } = this.props;

    const { outgoingWebhookStore } = store;

    outgoingWebhookStore.updateItems(filters).then(() => {
      if (isOnMount) {
        this.parseQueryParams();
      }
    });
  };

  renderTeam(record: OutgoingWebhook, teams: any) {
    return <TeamName team={teams[record.team]} />;
  }

  renderActionButtons = (record: ActionDTO) => {
    return (
      <HorizontalGroup justify="flex-end">
        <WithPermissionControlTooltip key={'edit_action'} userAction={UserActions.OutgoingWebhooksWrite}>
          <Button onClick={this.getEditClickHandler(record.id)} fill="text">
            Edit
          </Button>
        </WithPermissionControlTooltip>
        <WithPermissionControlTooltip key={'delete_action'} userAction={UserActions.OutgoingWebhooksWrite}>
          <WithConfirm>
            <Button onClick={this.getDeleteClickHandler(record.id)} fill="text" variant="destructive">
              Delete
            </Button>
          </WithConfirm>
        </WithPermissionControlTooltip>
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
    const { history } = this.props;

    return () => {
      this.setState({ outgoingWebhookIdToEdit: id });

      history.push(`${PLUGIN_ROOT}/outgoing_webhooks/${id}`);
    };
  };

  handleOutgoingWebhookFormHide = () => {
    const { history } = this.props;
    this.setState({ outgoingWebhookIdToEdit: undefined });

    history.push(`${PLUGIN_ROOT}/outgoing_webhooks`);
  };
}

export { OutgoingWebhooks };

export default withRouter(withMobXProviderContext(OutgoingWebhooks));
