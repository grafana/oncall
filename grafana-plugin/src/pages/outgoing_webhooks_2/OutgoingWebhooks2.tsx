import React from 'react';

import { Button, HorizontalGroup, Icon, IconButton, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import moment from 'moment-timezone';
import LegacyNavHeading from 'navbar/LegacyNavHeading';
import CopyToClipboard from 'react-copy-to-clipboard';
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
import OutgoingWebhook2Form from 'containers/OutgoingWebhook2Form/OutgoingWebhook2Form';
import OutgoingWebhook2Status from 'containers/OutgoingWebhook2Status/OutgoingWebhook2Status';
import RemoteFilters from 'containers/RemoteFilters/RemoteFilters';
import TeamName from 'containers/TeamName/TeamName';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ActionDTO } from 'models/action';
import { FiltersValues } from 'models/filters/filters.types';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { OutgoingWebhook2 } from 'models/outgoing_webhook_2/outgoing_webhook_2.types';
import { AppFeature } from 'state/features';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { isUserActionAllowed, UserActions } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';

import styles from './OutgoingWebhooks2.module.css';

const cx = cn.bind(styles);

const Action = {
  STATUS: 'status',
  EDIT: 'edit',
  COPY: 'copy',
};

interface OutgoingWebhooks2Props
  extends WithStoreProps,
    PageProps,
    RouteComponentProps<{ id: string; action: string }> {}

interface OutgoingWebhooks2State extends PageBaseState {
  outgoingWebhook2Action?: 'new' | 'update';
  outgoingWebhook2Id?: OutgoingWebhook2['id'];
}

@observer
class OutgoingWebhooks2 extends React.Component<OutgoingWebhooks2Props, OutgoingWebhooks2State> {
  state: OutgoingWebhooks2State = {
    errorData: initErrorDataState(),
  };

  componentDidUpdate(prevProps: OutgoingWebhooks2Props) {
    if (prevProps.match.params.id !== this.props.match.params.id) {
      this.parseQueryParams();
    }
  }

  parseQueryParams = async () => {
    this.setState((_prevState) => ({
      errorData: initErrorDataState(),
      outgoingWebhook2Id: undefined,
    })); // reset state on query parse

    const {
      store,
      match: {
        params: { id, action },
      },
    } = this.props;

    if (!id) {
      return;
    }

    let outgoingWebhook2: OutgoingWebhook2 | void = undefined;
    const isNewWebhook = id === 'new';

    if (!isNewWebhook) {
      outgoingWebhook2 = await store.outgoingWebhook2Store
        .loadItem(id, true)
        .catch((error) => this.setState({ errorData: { ...getWrongTeamResponseInfo(error) } }));
    }

    if (isNewWebhook || (action === Action.COPY && outgoingWebhook2)) {
      this.setState({ outgoingWebhook2Id: id, outgoingWebhook2Action: 'new' });
    } else if (action === Action.EDIT && outgoingWebhook2) {
      this.setState({ outgoingWebhook2Id: id, outgoingWebhook2Action: 'update' });
    } else if (action === Action.STATUS && outgoingWebhook2) {
      this.setState({ outgoingWebhook2Id: id, outgoingWebhook2Action: undefined });
    }
  };

  update = () => {
    const { store } = this.props;

    return store.outgoingWebhook2Store.updateItems();
  };

  render() {
    const { store, query } = this.props;
    const { outgoingWebhook2Id, outgoingWebhook2Action, errorData } = this.state;

    const webhooks = store.outgoingWebhook2Store.getSearchResult();

    const columns = [
      {
        width: '25%',
        title: 'Name',
        dataIndex: 'name',
        render: this.renderName,
      },
      {
        width: '5%',
        title: 'Trigger type',
        dataIndex: 'trigger_type_name',
      },
      {
        width: '5%',
        title: 'HTTP method',
        dataIndex: 'http_method',
      },
      {
        width: '35%',
        title: 'URL',
        dataIndex: 'url',
        render: this.renderUrl,
      },
      {
        width: '10%',
        title: 'Last run',
        render: this.renderLastRun,
      },
      {
        width: '15%',
        title: 'Team',
        render: (item: OutgoingWebhook) => this.renderTeam(item, store.grafanaTeamStore.items),
      },
      {
        width: '20%',
        key: 'action',
        render: this.renderActionButtons,
      },
    ];

    return store.hasFeature(AppFeature.Webhooks2) ? (
      <PageErrorHandlingWrapper
        errorData={errorData}
        objectName="outgoing webhook 2"
        pageName="outgoing_webhooks_2"
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
                    <div className="header__title">
                      <VerticalGroup spacing="sm">
                        <LegacyNavHeading>
                          <Text.Title level={3}>Outgoing Webhooks 2</Text.Title>
                        </LegacyNavHeading>
                        <Text type="secondary" className={cx('header__desc')}>
                          <Icon name="exclamation-triangle"></Icon> Preview Functionality! Things will change and things
                          will break! Do not use for critical production processes!
                        </Text>
                      </VerticalGroup>
                    </div>

                    <div className="u-pull-right">
                      <PluginLink
                        query={{ page: 'outgoing_webhooks_2', id: 'new' }}
                        disabled={!isUserActionAllowed(UserActions.OutgoingWebhooksWrite)}
                      >
                        <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                          <Button variant="primary" icon="plus">
                            Create
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
            {outgoingWebhook2Id && outgoingWebhook2Action && (
              <OutgoingWebhook2Form
                id={outgoingWebhook2Id}
                action={outgoingWebhook2Action}
                onUpdate={this.update}
                onHide={this.handleOutgoingWebhookFormHide}
              />
            )}
            {outgoingWebhook2Id && !outgoingWebhook2Action && (
              <OutgoingWebhook2Status
                id={outgoingWebhook2Id}
                onUpdate={this.update}
                onHide={this.handleOutgoingWebhookFormHide}
              />
            )}
          </>
        )}
      </PageErrorHandlingWrapper>
    ) : (
      <Text>Outgoing webhooks 2 functionality is not enabled.</Text>
    );
  }

  renderOutgoingWebhooksFilters() {
    const { query, store } = this.props;
    return (
      <div className={cx('filters')}>
        <RemoteFilters
          query={query}
          page="webhooks"
          grafanaTeamStore={store.grafanaTeamStore}
          onChange={this.handleFiltersChange}
        />
      </div>
    );
  }

  handleFiltersChange = (filters: FiltersValues, isOnMount) => {
    const { store } = this.props;

    const { outgoingWebhook2Store } = store;

    outgoingWebhook2Store.updateItems(filters).then(() => {
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
        <CopyToClipboard text={record.id}>
          <IconButton
            variant="primary"
            tooltip={
              <div>
                ID {record.id}
                <br />
                (click to copy ID to clipboard)
              </div>
            }
            tooltipPlacement="top"
            name="info-circle"
          />
        </CopyToClipboard>
        <WithPermissionControlTooltip key={'status_action'} userAction={UserActions.OutgoingWebhooksRead}>
          <Button onClick={() => this.onStatusClick(record.id)} fill="text">
            Status
          </Button>
        </WithPermissionControlTooltip>
        <WithPermissionControlTooltip key={'edit_action'} userAction={UserActions.OutgoingWebhooksWrite}>
          <Button onClick={() => this.onEditClick(record.id)} fill="text">
            Edit
          </Button>
        </WithPermissionControlTooltip>
        <WithPermissionControlTooltip key={'copy_action'} userAction={UserActions.OutgoingWebhooksWrite}>
          <Button onClick={() => this.onCopyClick(record.id)} fill="text">
            Make a copy
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

  renderName(name: String) {
    return (
      <div className="u-break-word">
        <span>{name}</span>
      </div>
    );
  }

  renderUrl(url: string) {
    return (
      <div className="u-break-word">
        <span>{url}</span>
      </div>
    );
  }

  renderLastRun(record: OutgoingWebhook2) {
    const lastRunMoment = moment(record.last_response_log?.timestamp);

    return !record.is_webhook_enabled ? (
      <Text type="secondary">Disabled</Text>
    ) : (
      <VerticalGroup spacing="none">
        <Text type="secondary">{lastRunMoment.isValid() ? lastRunMoment.format('MMM DD, YYYY') : '-'}</Text>
        <Text type="secondary">{lastRunMoment.isValid() ? lastRunMoment.format('hh:mm A') : ''}</Text>
        <Text type="secondary">
          {lastRunMoment.isValid()
            ? record.last_response_log?.status_code
              ? 'Status: ' + record.last_response_log?.status_code
              : 'Check Status'
            : ''}
        </Text>
      </VerticalGroup>
    );
  }

  getDeleteClickHandler = (id: OutgoingWebhook2['id']) => {
    const { store } = this.props;

    return () => {
      store.outgoingWebhook2Store.delete(id).then(this.update);
    };
  };

  onEditClick = (id: OutgoingWebhook2['id']) => {
    const { history } = this.props;

    this.setState({ outgoingWebhook2Id: id, outgoingWebhook2Action: 'update' });

    history.push(`${PLUGIN_ROOT}/outgoing_webhooks_2/edit/${id}`);
  };

  onCopyClick = (id: OutgoingWebhook2['id']) => {
    const { history } = this.props;

    this.setState({ outgoingWebhook2Id: id, outgoingWebhook2Action: 'new' });

    history.push(`${PLUGIN_ROOT}/outgoing_webhooks_2/copy/${id}`);
  };

  onStatusClick = (id: OutgoingWebhook2['id']) => {
    const { history } = this.props;

    this.setState({ outgoingWebhook2Id: id, outgoingWebhook2Action: undefined });

    history.push(`${PLUGIN_ROOT}/outgoing_webhooks_2/status/${id}`);
  };

  handleOutgoingWebhookFormHide = () => {
    const { history } = this.props;

    this.setState({ outgoingWebhook2Id: undefined, outgoingWebhook2Action: undefined });

    history.push(`${PLUGIN_ROOT}/outgoing_webhooks_2`);
  };
}

export { OutgoingWebhooks2 };

export default withRouter(withMobXProviderContext(OutgoingWebhooks2));
